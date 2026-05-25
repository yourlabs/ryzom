'''
Defines the django signals handlers.
'''
import time
import traceback

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ryzom_django_channels import celery_app, locks

from ryzom_django_channels.components import model_templates
from ryzom_django_channels.ddp import send_change, send_insert, send_remove
from ryzom_django_channels.models import Subscription
from ryzom_django_channels.pubsub import Publishable


def try_task(fn, *args, **kwargs):
    retry = 5
    while retry:
        try:
            fn(*args, **kwargs)
            break
        except Exception:
            traceback.print_exc()
            retry -= 1
            time.sleep(0.2)


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


def ddp_insert_change(sender_mod, sender_name, created, instance_id,
                      excluded_subs=None):
    subscriptions = Subscription.objects.filter(
        publication__model_class=sender_name,
        publication__model_module=sender_mod,
    )
    if excluded_subs:
        subscriptions = subscriptions.exclude(pk__in=excluded_subs)

    instance_id_str = str(instance_id)

    for sub in subscriptions:
        model = sub.publication.model
        template = model_templates[sub.subscriber.model_template]
        to_python = model.id.field.to_python

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
                send_remove(sub, template, model.objects.get(pk=to_python(id_str)))
            for id_str in inserted:
                send_insert(sub, template, qs.get(pk=to_python(id_str)))


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
    subscriptions = Subscription.objects.filter(
        publication__model_class=sender_name,
        publication__model_module=sender_mod,
    )
    if excluded_subs:
        subscriptions = subscriptions.exclude(pk__in=excluded_subs)

    instance_id_str = str(instance_id)

    for sub in subscriptions:
        model = sub.publication.model
        template = model_templates[sub.subscriber.model_template]
        to_python = model.id.field.to_python

        # Check membership on raw strings — avoids to_python() conversion
        if instance_id_str not in sub.qs:
            continue

        old_qs_strings = set(sub.qs)

        qs = sub.get_queryset()
        if not qs.query.can_filter():
            qs.query.clear_limits()

        new_qs_strings = set(sub.qs)

        removed = old_qs_strings - new_qs_strings
        inserted = new_qs_strings - old_qs_strings

        for id_str in removed:
            instance = model(id=instance_id)
            send_remove(sub, template, instance)
        for id_str in inserted:
            send_insert(sub, template, qs.get(pk=to_python(id_str)))
