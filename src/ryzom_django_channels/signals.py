'''
Defines the django signals handlers.
'''
import logging
import time

from django.db import transaction
from django.db.models.signals import post_delete, post_save
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


@celery_app.task()
def ddp_insert_change_task(sender_mod, sender_name, created, instance_id):
    try_task(
        ddp_insert_change,
        sender_mod, sender_name, created, instance_id
    )


@celery_app.task()
def ddp_delete_task(sender_mod, sender_name, instance_id):
    try_task(
        ddp_delete,
        sender_mod, sender_name, instance_id
    )


@receiver(post_save)
def _ddp_insert_change(sender, **kwargs):
    '''
    Function to send a DDP insert/change/remove messages to the channel layer
    whenever a Publishable model's save() method is called.
    This function will update the queryset of all subscriptions
    associated with the sender model and send insert, remove or change
    message for each id that was added or removed from the old
    queryset to the new one.
    '''
    if Publishable in sender.mro():
        instance = kwargs.get('instance')
        sender_mod = instance.__module__
        sender_name = instance.__class__.__name__
        created = kwargs.get('created')
        instance_id = str(instance.id)
        ddp_insert_change_task.delay(
            sender_mod,
            sender_name,
            created,
            instance_id
        )


def _locked_subscriptions(sender_mod, sender_name):
    '''Yield each matching Subscription, locked FOR UPDATE inside its own
    transaction.

    The whole insert/change/remove decision is a read-modify-write of the
    subscription's stored id list (``sub.qs``). Without a row lock, two
    concurrent ``Product.save()`` tasks — or a save racing a filter request —
    read the same baseline, both recompute, and both write, so the diff is
    taken against stale state and rows are missed or duplicated. Locking each
    subscription row serialises those writers per subscription.
    '''
    sub_ids = list(
        Subscription.objects.filter(
            publication__model_class=sender_name,
            publication__model_module=sender_mod,
        ).values_list('id', flat=True)
    )
    for sub_id in sub_ids:
        with transaction.atomic():
            # Lock only the Subscription row (no select_related): `client` is a
            # nullable FK, so joining it would make a LEFT OUTER JOIN that
            # Postgres refuses to lock ("FOR UPDATE cannot be applied to the
            # nullable side of an outer join"); joining `publication` would
            # over-lock the row shared by every subscriber. The relations
            # lazy-load unlocked, which is what we want.
            try:
                sub = Subscription.objects.select_for_update().get(pk=sub_id)
            except Subscription.DoesNotExist:
                # Raced with a client disconnect / unsubscribe between taking
                # the id snapshot and acquiring the lock — nothing to push.
                continue
            yield sub


def _push_window_delta(sub, changed_pk):
    '''Re-window the subscription and push the minimal DDP delta.

    Recomputes the subscription's window (a paginated subscriber stores only the
    visible page; a non-paginated one stores the whole filtered set) and diffs
    the old id list against the new one. A single base-row event changes a
    window by at most: one row leaves + one row enters, plus the changed row's
    own content/position. Everything is expressed with the existing
    insert(position) / change(id) / remove(id) ops; ``position`` is the index
    within the (re)stored window.

    See ``PAGINATION.md`` for the window-ripple reasoning.
    '''
    template = model_templates[sub.subscriber.model_template]
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
                send_change(sub, template, row)
            else:                            # moved within the window
                send_remove(sub, template, row)
                send_insert(sub, template, row)
        return

    # Removes first, so the subsequent insert positions land at the right child
    # index of the current DOM. A removed row usually still exists (filtered out
    # or evicted to the next page) -> push the real instance; only a genuinely
    # deleted row needs a bare shell (send_remove reads just its DOM id).
    existing = {obj.pk: obj for obj in model.objects.filter(pk__in=removed)}
    for pk in removed:
        send_remove(sub, template, existing.get(pk) or model(pk=pk))

    for pk in sorted(added, key=new_window.index):
        row = fetch(pk)
        if row is not None:
            send_insert(sub, template, row)

    # Changed row stayed in the window while a boundary rippled: refresh it.
    if changed_pk in new_set and changed_pk not in added:
        row = fetch(changed_pk)
        if row is not None:
            send_change(sub, template, row)


def ddp_insert_change(sender_mod, sender_name, created, instance_id):
    '''
    Route a single save to every subscription on that model.

    Non-paginated subscribers get the cheap ``filter(pk=...).exists()`` test:
    if the changed row neither was nor is a member of the filtered set, the set
    is unchanged and the subscription is skipped without a requery. Paginated
    subscribers re-window every time (their stored id list is the window, not
    the set, so "not in window" doesn't imply "didn't ripple the window" — a
    change above the page shifts it). Reducing that fan-out soundly needs the
    row's pre-change key; see ``PAGINATION.md`` §6.
    '''
    for sub in _locked_subscriptions(sender_mod, sender_name):
        model = sub.publication.model
        changed_pk = model.id.field.to_python(instance_id)

        if not getattr(sub.subscriber, 'paginate_by', None):
            was_in = changed_pk in sub.queryset
            base = sub.publication.publish_function(sub.client.user)
            now_in = sub.subscriber.get_queryset(
                sub.client.user, base.filter(pk=instance_id), sub.options,
            ).exists()
            if not was_in and not now_in:
                continue

        _push_window_delta(sub, changed_pk)


@receiver(post_delete)
def _ddp_delete(sender, **kwargs):
    '''
    Function to send a DDP insert/remove messages to the channel layer
    whenever a Publishable model's delete() method is called.
    This function will update the queryset of all subscriptions
    associated with the sender model and send insert and remove
    message for each id that was added or removed from the old
    queryset to the new one.
    '''
    if Publishable in sender.mro():
        instance = kwargs.get('instance')
        sender_mod = instance.__module__
        sender_name = instance.__class__.__name__
        instance_id = str(instance.id)
        ddp_delete_task.delay(
            sender_mod,
            sender_name,
            instance_id
        )


def ddp_delete(sender_mod, sender_name, instance_id):
    '''
    Route a delete to every subscription on that model.

    A non-paginated subscription that never listed the row is skipped. A
    paginated one re-windows regardless: deleting a row *above* the visible
    page shifts the window even though the deleted row isn't on it.
    '''
    for sub in _locked_subscriptions(sender_mod, sender_name):
        model = sub.publication.model
        changed_pk = model.id.field.to_python(instance_id)

        if (not getattr(sub.subscriber, 'paginate_by', None)
                and changed_pk not in sub.queryset):
            continue

        _push_window_delta(sub, changed_pk)
