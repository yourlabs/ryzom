'''
Defines the django signals handlers.
'''
import logging
import time

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ryzom_django_channels import celery_app, locks

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
            break
        except Exception:
            logger.exception('ryzom ddp task failed (%s retries left)', retry - 1)
            retry -= 1
            time.sleep(0.2)


def _has_subscriptions(sender_mod, sender_name):
    '''
    Cheap pre-check: most Publishable saves (audit logs, background
    bookkeeping) happen with nobody subscribed. One indexed EXISTS query
    here avoids a Redis round-trip + a Celery task dispatch per save.
    '''
    return Subscription.objects.filter(
        publication__model_class=sender_name,
        publication__model_module=sender_mod,
    ).exists()


@celery_app.task()
def ddp_insert_change_task(sender_mod, sender_name, created, instance_id,
                           excluded_subs=None):
    try_task(
        ddp_insert_change,
        sender_mod, sender_name, created, instance_id, excluded_subs,
    )


@celery_app.task()
def ddp_delete_task(sender_mod, sender_name, instance_id, excluded_subs=None):
    try_task(
        ddp_delete,
        sender_mod, sender_name, instance_id, excluded_subs,
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
    if Publishable not in sender.mro():
        return

    instance = kwargs.get('instance')
    sender_mod = instance.__module__
    sender_name = instance.__class__.__name__

    if not _has_subscriptions(sender_mod, sender_name):
        return

    created = kwargs.get('created')
    instance_id = str(instance.id)

    locked = locks.locked_subs_for_model(sender_mod, sender_name)
    if locked:
        event = {
            'op': 'save',
            'created': bool(created),
            'instance_id': instance_id,
        }
        for sub_id in locked:
            locks.enqueue(sub_id, event)

    ddp_insert_change_task.delay(
        sender_mod,
        sender_name,
        created,
        instance_id,
        list(locked) if locked else None,
    )


def for_each_subscription(sender_mod, sender_name, excluded_subs, handler):
    '''
    Run ``handler(sub, model, template, to_python)`` for every subscription
    on the given model, each call inside its own transaction holding a row
    lock on the Subscription.

    The row lock serializes concurrent DDP tasks per subscription: without
    it, two tasks triggered by near-simultaneous saves both snapshot the
    same stale `qs`, both compute a delta against it, and the client
    receives duplicate inserts (or misses removes). Locking the row makes
    snapshot → recompute → send atomic per subscription.

    Subscriptions are processed independently: an exception while handling
    one (bad template, vanished client...) is logged and does not prevent
    the others from receiving their updates.
    '''
    sub_ids = Subscription.objects.filter(
        publication__model_class=sender_name,
        publication__model_module=sender_mod,
    ).values_list('pk', flat=True)
    if excluded_subs:
        sub_ids = sub_ids.exclude(pk__in=excluded_subs)

    for sub_id in list(sub_ids):
        try:
            with transaction.atomic():
                sub = (
                    Subscription.objects
                    # of=('self',): client/user are nullable FKs (outer
                    # joins), which FOR UPDATE can't lock — and we only
                    # need to serialize on the subscription row anyway.
                    .select_for_update(of=('self',))
                    .select_related('publication', 'client', 'client__user')
                    .filter(pk=sub_id)
                    .first()
                )
                if sub is None or sub.client is None:
                    # reaped concurrently / client gone: nothing to notify
                    continue
                model = sub.publication.model
                template = model_templates[sub.subscriber.model_template]
                to_python = model.id.field.to_python
                handler(sub, model, template, to_python)
        except Exception:
            logger.exception(
                'ryzom: subscription %s failed to process %s.%s update',
                sub_id, sender_mod, sender_name,
            )


def ddp_insert_change(sender_mod, sender_name, created, instance_id,
                      excluded_subs=None):
    instance_id_str = str(instance_id)

    def handle(sub, model, template, to_python):
        # Snapshot raw string IDs before get_queryset() updates them
        old_qs_strings = set(sub.qs)

        qs = sub.get_queryset()
        if not qs.query.can_filter():
            qs.query.clear_limits()

        # Compare raw strings — avoids redundant to_python() conversions
        new_qs_strings = set(sub.qs)

        inserted = new_qs_strings - old_qs_strings
        removed = old_qs_strings - new_qs_strings

        if not inserted and not removed:
            if instance_id_str in new_qs_strings:
                send_change(sub, template, qs.get(pk=instance_id))
        else:
            for id_str in removed:
                # The row usually still exists (it merely left this
                # subscription's queryset); fall back to a pk-only stub if
                # it was deleted in between — send_remove only needs the
                # component id (see template dom_id support in ddp.py).
                obj = model.objects.filter(pk=to_python(id_str)).first()
                if obj is None:
                    obj = model(id=to_python(id_str))
                send_remove(sub, template, obj)
            for id_str in inserted:
                send_insert(sub, template, qs.get(pk=to_python(id_str)))
            if (instance_id_str in new_qs_strings
                    and instance_id_str not in inserted):
                # The save that triggered us also changed this instance's
                # rendering even though its membership didn't change (the
                # inserts/removes above concern *other* rows shifting in or
                # out of a windowed queryset).
                send_change(sub, template, qs.get(pk=instance_id))

    for_each_subscription(sender_mod, sender_name, excluded_subs, handle)


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
    if Publishable not in sender.mro():
        return

    instance = kwargs.get('instance')
    sender_mod = instance.__module__
    sender_name = instance.__class__.__name__

    if not _has_subscriptions(sender_mod, sender_name):
        return

    instance_id = str(instance.id)

    locked = locks.locked_subs_for_model(sender_mod, sender_name)
    if locked:
        event = {'op': 'delete', 'instance_id': instance_id}
        for sub_id in locked:
            locks.enqueue(sub_id, event)

    ddp_delete_task.delay(
        sender_mod,
        sender_name,
        instance_id,
        list(locked) if locked else None,
    )


def ddp_delete(sender_mod, sender_name, instance_id, excluded_subs=None):
    def handle(sub, model, template, to_python):
        # NOTE: no early-exit on `instance_id not in sub.qs` — deleting a
        # row *outside* a windowed (paginated) queryset can still shift
        # rows into the window, so the delta must always be recomputed.
        old_qs_strings = set(sub.qs)

        qs = sub.get_queryset()
        if not qs.query.can_filter():
            qs.query.clear_limits()

        new_qs_strings = set(sub.qs)

        removed = old_qs_strings - new_qs_strings
        inserted = new_qs_strings - old_qs_strings

        for id_str in removed:
            # The deleted row is gone from the DB; rows that shifted out of
            # a window still exist. Either way send_remove only needs the
            # component id, which dom_id-aware templates derive from the pk.
            obj = model.objects.filter(pk=to_python(id_str)).first()
            if obj is None:
                obj = model(id=to_python(id_str))
            send_remove(sub, template, obj)
        for id_str in inserted:
            send_insert(sub, template, qs.get(pk=to_python(id_str)))

    for_each_subscription(sender_mod, sender_name, excluded_subs, handle)
