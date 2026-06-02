'''
Django signal handlers: route a base-row change to the live subscriptions it
affects and push each one's minimal DDP delta.

The routing is a *reverse query* (PROBLEM.md §3): instead of re-running every
standing query on every write, we ask "which subscriptions' filters does this
one row match?" and visit only those. A subscription is a candidate iff the
changed row matches its filter with its new OR old values (the window is
irrelevant to candidacy — see MATCHING.md). Candidate selection runs here, in
the saving process, reusing each subscriber's declared facets in reverse; the
Celery worker then locks each candidate and computes its window delta.
'''
import importlib
import logging
import time

from django.db import transaction
from django.db.models import Q
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from ryzom_django_channels import celery_app

from ryzom_django_channels.components import model_templates
from ryzom_django_channels.ddp import send_change, send_insert, send_remove
from ryzom_django_channels.models import Subscription
from ryzom_django_channels.pubsub import Publishable

logger = logging.getLogger(__name__)


def try_task(fn, *args, **kwargs):
    retry = 5
    while retry:
        try:
            fn(*args, **kwargs)
            return
        except Exception:
            retry -= 1
            logger.exception(
                '%s failed, %d attempt(s) left',
                getattr(fn, '__name__', fn), retry,
            )
            time.sleep(0.2)
    # All retries exhausted. The push is lost, so a connected client's DOM now
    # silently diverges from the database until the page is reloaded. Surface
    # it loudly instead of swallowing it with a bare print().
    logger.error(
        '%s permanently failed after retries; a connected client DOM is '
        'now stale (reload required)', getattr(fn, '__name__', fn),
    )


# --- candidate selection: the reverse query --------------------------------

def _snapshot(instance):
    '''A plain dict of the instance's field values for reverse facet matching,
    so the match never depends on the live (possibly deleted) instance.

    Values are coerced to the field's Python type: a freshly created instance
    may still hold raw assigned values (e.g. a form string ``"5"`` for an
    IntegerField, which Postgres coerces on insert but Python does not), and the
    facet predicates compare against typed values.
    '''
    def typed(field):
        value = getattr(instance, field.attname)
        try:
            return field.to_python(value)
        except (TypeError, ValueError):
            return value
    return {field.attname: typed(field) for field in instance._meta.concrete_fields}


def _candidate_ids(sender_mod, sender_name, old, new):
    '''Ids of the subscriptions a change to this row can affect.

    Grouped by subscriber class so each class's own facets drive the match. A
    subscriber that declares no facets has an unknown filter, so every change to
    the model is a potential affect -> all of its subscriptions are candidates
    (no worse than the previous "visit all"). A faceted subscriber is matched in
    reverse against the row's new and old values; their union is the candidate
    set (covers out->in via `new` and in->out via `old`).
    '''
    base = Subscription.objects.filter(
        publication__model_module=sender_mod,
        publication__model_class=sender_name,
    )
    ids = set()
    seen = base.values_list('subscriber_module', 'subscriber_class').distinct()
    for mod_name, cls_name in seen:
        subscriber = getattr(importlib.import_module(mod_name), cls_name)
        subs = base.filter(subscriber_module=mod_name, subscriber_class=cls_name)
        facets = getattr(subscriber, 'facets', None)
        if not facets:
            ids.update(subs.values_list('id', flat=True))
            continue
        for row in (old, new):
            if row is None:
                continue
            annotations, predicate = {}, Q()
            for facet in facets:
                ann, q = facet.candidate(row)
                annotations.update(ann)
                predicate &= q
            ids.update(
                subs.annotate(**annotations)
                .filter(predicate)
                .values_list('id', flat=True)
            )
    return ids


@receiver(pre_save)
def _ddp_capture_old(sender, instance, **kwargs):
    '''Snapshot the pre-change row so the post_save handler can also route to
    subscriptions whose filter the row matched *before* the change (the in->out
    transition), which the new values alone can't reveal.'''
    if Publishable in sender.mro():
        instance._ddp_old = None
        if instance.pk is not None:
            old = sender.objects.filter(pk=instance.pk).first()
            if old is not None:
                instance._ddp_old = _snapshot(old)


@receiver(post_save)
def _ddp_insert_change(sender, instance, created, **kwargs):
    if Publishable not in sender.mro():
        return
    old = None if created else getattr(instance, '_ddp_old', None)
    ids = _candidate_ids(
        instance.__module__, type(instance).__name__,
        old, _snapshot(instance),
    )
    if ids:
        ddp_process_task.delay(
            instance.__module__, type(instance).__name__,
            str(instance.pk), list(ids),
        )


@receiver(post_delete)
def _ddp_delete(sender, instance, **kwargs):
    if Publishable not in sender.mro():
        return
    ids = _candidate_ids(
        instance.__module__, type(instance).__name__,
        _snapshot(instance), None,
    )
    if ids:
        ddp_process_task.delay(
            instance.__module__, type(instance).__name__,
            str(instance.pk), list(ids),
        )


# --- delta computation: run in the worker over the routed candidates --------

@celery_app.task()
def ddp_process_task(sender_mod, sender_name, instance_id, candidate_ids):
    try_task(ddp_process, sender_mod, sender_name, instance_id, candidate_ids)


def ddp_process(sender_mod, sender_name, instance_id, candidate_ids):
    '''Push each routed candidate's window delta.

    Candidate selection (the reverse facet match) already happened in the
    saving process; here we only lock each candidate row and diff its window.
    '''
    for sub_id in candidate_ids:
        with transaction.atomic():
            # Lock only the Subscription row (no select_related): `client` is a
            # nullable FK, so joining it would make a LEFT OUTER JOIN Postgres
            # refuses to lock; `publication` is shared and would over-lock.
            sub = (
                Subscription.objects
                .select_for_update()
                .filter(pk=sub_id)
                .first()
            )
            if sub is None:
                # Disconnected / unsubscribed between selection and the lock.
                continue
            changed_pk = sub.publication.model.id.field.to_python(instance_id)
            _push_window_delta(sub, changed_pk)


def iter_window_ops(sub, changed_pk):
    '''Re-window the subscription and yield its minimal delta as transport-neutral
    ops, **without sending anything**.

    Recomputes the subscription's window (a paginated subscriber stores only the
    visible page; a non-paginated one stores the whole filtered set) and diffs
    the old id list against the new one. A single base-row event changes a
    window by at most: one row leaves + one row enters, plus the changed row's
    own content/position.

    Yields ``(kind, instance)`` pairs, ``kind`` in
    ``'insert' | 'change' | 'remove'``, in apply order (removes before the
    inserts whose positions assume them). The same diff feeds two emitters: the
    channel-layer push (``_push_window_delta``) and the client-pull poll
    response (see ``POLLING.md``). ``position`` for an insert/change is read off
    the freshly persisted window by the emitter, exactly as before; this
    generator persists that window (via ``get_queryset``) before yielding any op.

    See ``PAGINATION.md`` for the window-ripple reasoning.
    '''
    model = sub.publication.model

    old_window = list(sub.queryset)
    sub.get_queryset()                      # recompute + persist the new window
    new_window = list(sub.queryset)

    old_set, new_set = set(old_window), set(new_window)
    removed = old_set - new_set
    added = new_set - old_set

    # A row to insert/change can be deleted by a concurrent event between the
    # re-window and this fetch; skip it then (a later task reconciles).
    row_qs = sub.row_queryset()

    def fetch(pk):
        return row_qs.filter(pk=pk).first()

    if not removed and not added:
        # Same membership: only the changed row's content and/or position moved.
        row = fetch(changed_pk) if changed_pk in new_set else None
        if row is not None:
            if old_window.index(changed_pk) == new_window.index(changed_pk):
                yield ('change', row)
            else:                            # moved within the window
                yield ('remove', row)
                yield ('insert', row)
        return

    # Removes first, so the subsequent insert positions land at the right child
    # index of the current DOM. A removed row usually still exists (filtered out
    # or evicted to the next page) -> emit the real instance; only a genuinely
    # deleted row needs a bare shell (remove reads just its DOM id).
    existing = {obj.pk: obj for obj in model.objects.filter(pk__in=removed)}
    for pk in removed:
        yield ('remove', existing.get(pk) or model(pk=pk))

    for pk in sorted(added, key=new_window.index):
        row = fetch(pk)
        if row is not None:
            yield ('insert', row)

    # Changed row stayed in the window while a boundary rippled: refresh it.
    if changed_pk in new_set and changed_pk not in added:
        row = fetch(changed_pk)
        if row is not None:
            yield ('change', row)


_SEND = {'insert': send_insert, 'change': send_change, 'remove': send_remove}


def _push_window_delta(sub, changed_pk):
    '''Push a subscription's window delta over the channel layer (the websocket
    transport): a thin channel-layer emitter over ``iter_window_ops``.'''
    template = model_templates[sub.subscriber.model_template]
    for kind, instance in iter_window_ops(sub, changed_pk):
        _SEND[kind](sub, template, instance)
