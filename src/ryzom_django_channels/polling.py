'''
Client-pull (polling) transport.

The constraint (see POLLING.md): no server-initiated communication. So instead
of the push path running the window diff on every write and speaking unprompted
over the channel layer, the browser asks "what changed for me?" on its own
schedule and the server only ever *responds*. ``poll_client`` computes that
response: for each of the client's subscriptions it re-windows and diffs against
the stored state, returning the same ``{type, params}`` DDP messages the
websocket would have pushed (``ddp.client_message``), which the client applies
through the unchanged ``ryzom.js:handleDDP``.

Two differences from the push path (``signals.iter_window_ops``):

- there is no single ``changed_pk`` — many writes may have accrued since the
  last poll — so the diff is over the whole window, not one row;
- to keep an *idle* poll empty (no flicker), a content change of a row that
  stayed in the window is detected by a per-row fingerprint stored on the
  subscription, not by knowing which row was saved.
'''
import hashlib
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from ryzom_django_channels.components import model_templates
from ryzom_django_channels.ddp import client_message
from ryzom_django_channels.models import Client, Subscription


def _fingerprint(instance):
    '''A content hash of a row's concrete field values.

    The row template is a pure function of these fields, so the fingerprint
    flips iff a change would alter the rendered row -> the poll emits a
    ``change`` only for rows whose content actually changed, keeping an idle
    poll empty.
    '''
    parts = [
        f'{field.attname}={getattr(instance, field.attname)!r}'
        for field in instance._meta.concrete_fields
    ]
    return hashlib.md5('|'.join(parts).encode()).hexdigest()


def subscription_delta(sub):
    '''The pending DDP messages bringing one subscription's client DOM in line.

    Mirrors the push diff but is order- and content-aware over an arbitrary
    multi-write delta. Removes-first then inserts-in-ascending-window-position
    is the same reconciliation the filter/pager already rely on; a genuine
    *reorder* of surviving rows (a sort-key edit crossing two in-window rows)
    can't be expressed cleanly with position ops, so that rare case replaces the
    whole window (always correct, never hit on an idle poll).
    '''
    template = model_templates[sub.subscriber.model_template]
    model = sub.publication.model

    old_window = list(sub.queryset)
    old_fp = dict((sub.options or {}).get('_fp') or {})

    new_rows = sub.get_queryset()             # recompute + persist new window
    rows = {obj.pk: obj for obj in new_rows}
    new_window = list(sub.queryset)

    old_set, new_set = set(old_window), set(new_window)
    # Fresh fingerprint baseline for the whole new window (next poll compares
    # against this); JSON object keys are strings, so key by str(pk).
    new_fp = {str(pk): _fingerprint(rows[pk]) for pk in new_window if pk in rows}

    messages = []

    stayed_old_order = [pk for pk in old_window if pk in new_set]
    stayed_new_order = [pk for pk in new_window if pk in old_set]

    if stayed_old_order != stayed_new_order:
        # Surviving rows reordered -> full window replace.
        existing = {o.pk: o for o in model.objects.filter(pk__in=old_set)}
        for pk in old_window:
            messages.append(client_message(
                sub, template, 'remove', existing.get(pk) or model(pk=pk)))
        for pk in new_window:
            obj = rows.get(pk)
            if obj is not None:
                messages.append(client_message(sub, template, 'insert', obj))
    else:
        removed = old_set - new_set
        added = new_set - old_set
        existing = {o.pk: o for o in model.objects.filter(pk__in=removed)}
        for pk in removed:
            messages.append(client_message(
                sub, template, 'remove', existing.get(pk) or model(pk=pk)))
        for pk in sorted(added, key=new_window.index):
            obj = rows.get(pk)
            if obj is not None:
                messages.append(client_message(sub, template, 'insert', obj))
        # In-place content changes of surviving rows. A row with no prior
        # fingerprint was just server-rendered (or just inserted above), so its
        # DOM is already fresh -> don't re-emit it.
        for pk in old_set & new_set:
            obj = rows.get(pk)
            if obj is None:
                continue
            key = str(pk)
            if key in old_fp and old_fp[key] != new_fp.get(key):
                messages.append(client_message(sub, template, 'change', obj))

    opts = dict(sub.options or {})
    opts['_fp'] = new_fp
    sub.options = opts
    sub.save(update_fields=['options'])

    return messages


def poll_client(client):
    '''All pending DDP messages for a polling client, advancing its stored state.

    Each subscription is diffed under its own row lock (as the push worker does)
    so a concurrent write can't interleave the read-modify-write of its window.
    Registration (single-object) polling is not handled yet — see POLLING.md.
    '''
    client.last_seen = timezone.now()
    client.save(update_fields=['last_seen'])

    messages = []
    sub_ids = list(
        Subscription.objects.filter(client=client).values_list('id', flat=True)
    )
    for sub_id in sub_ids:
        with transaction.atomic():
            sub = (
                Subscription.objects
                .select_for_update()
                .filter(pk=sub_id)
                .first()
            )
            if sub is None:
                continue
            messages.extend(subscription_delta(sub))
    return messages


def sweep_stale_clients(ttl_seconds):
    '''Reclaim polling clients that stopped polling.

    A push client is deleted on websocket disconnect; a polling client has no
    disconnect, so one whose ``last_seen`` is older than the TTL is assumed gone
    and deleted (cascading its subscriptions). Push clients have a NULL
    ``last_seen`` and are never touched here.
    '''
    cutoff = timezone.now() - timedelta(seconds=ttl_seconds)
    Client.objects.filter(
        last_seen__isnull=False, last_seen__lt=cutoff,
    ).delete()
