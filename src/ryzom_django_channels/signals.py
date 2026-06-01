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


def ddp_insert_change(sender_mod, sender_name, created, instance_id):
    '''
    Route a single save to every subscription on that model.

    For each subscription we ask one cheap, indexed question — "does the row
    that just changed belong in *this* subscription's filtered set?" — by
    reusing the subscription's own ``get_queryset`` scoped to the changed pk
    (``filter(pk=...).exists()``). Subscriptions the change can't affect (the
    row neither was nor is a member) are skipped without recomputing their
    queryset. Only an affected subscription pays the ordered requery needed to
    keep its stored id list and compute the DOM insert/change position.

    Note: there is no LIMIT today, so the affected-branch requery is the full
    set. Real pagination (ORDER BY + LIMIT windows) needs explicit boundary
    handling and replaces that step — deliberately out of scope here.
    '''
    for sub in _locked_subscriptions(sender_mod, sender_name):
        model = sub.publication.model
        template = model_templates[sub.subscriber.model_template]
        changed_pk = model.id.field.to_python(instance_id)

        was_in = changed_pk in sub.queryset
        # Cheap reverse test: reuse the publication base + the subscription's
        # own filter (the single source of truth), scoped to just this row.
        base = sub.publication.publish_function(sub.client.user)
        now_in = sub.subscriber.get_queryset(
            sub.client.user,
            base.filter(pk=instance_id),
            sub.options,
        ).exists()

        if not was_in and not now_in:
            # Row is outside this subscription's set before and after: nothing
            # to push. The common case, answered by one indexed EXISTS instead
            # of a full requery + whole-set diff.
            continue

        # Affected: refresh the stored ordered id list so the diff and the
        # insert/change position stay correct.
        qs = sub.get_queryset()
        if not qs.query.can_filter():
            qs.query.clear_limits()

        if was_in and now_in:
            # Still a member; its content (and possibly sort position) changed.
            send_change(sub, template, qs.get(pk=instance_id))
        elif now_in:
            # Newly matches the filter -> it appears in the list.
            send_insert(sub, template, qs.get(pk=instance_id))
        else:
            # No longer matches the filter -> it leaves the list. The row still
            # exists (only filtered out), so push the real, live instance.
            send_remove(sub, template, model.objects.get(pk=instance_id))


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
    Route a delete to every subscription that currently lists the row.

    A delete can only remove the row from a set (and, under a future LIMIT,
    pull the next row up into the window), so subscriptions that never listed
    it are skipped after the in-memory membership check — no requery needed.
    '''
    for sub in _locked_subscriptions(sender_mod, sender_name):
        model = sub.publication.model
        template = model_templates[sub.subscriber.model_template]
        changed_pk = model.id.field.to_python(instance_id)

        old_qs = sub.queryset
        if changed_pk not in old_qs:
            # This subscription never listed the deleted row.
            continue

        qs = sub.get_queryset()
        if not qs.query.can_filter():
            qs.query.clear_limits()
        new_qs = sub.queryset

        for pk in set(old_qs) - set(new_qs):
            # The deleted row (and, under a LIMIT, any row pushed out of the
            # window). The row is gone from the DB, so hand send_remove a bare
            # shell purely to derive the row's DOM id.
            send_remove(sub, template, model(pk=pk))
        for pk in set(new_qs) - set(old_qs):
            # Only under a LIMIT: a row pulled up into the visible window.
            send_insert(sub, template, qs.get(pk=pk))
