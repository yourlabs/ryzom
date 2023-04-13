'''
Defines the django signals handlers.
'''
import time

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ryzom_django_channels import celery_app

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
        except Exception as e:
            print(e)
            retry -= 1
            time.sleep(0.2)


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


def ddp_insert_change(sender_mod, sender_name, created, instance_id):
    print('ddp_insert_change')
    subscriptions = Subscription.objects.filter(
        publication__model_class=sender_name,
        publication__model_module=sender_mod
    )

    for sub in subscriptions:
        model = sub.publication.model
        template = model_templates[sub.subscriber.model_template]
        old_qs = sub.queryset

        qs = sub.get_queryset()
        if not qs.query.can_filter():
            qs.query.clear_limits()

        new_qs = sub.queryset

        diff = {
            'inserted': set(new_qs).difference(set(old_qs)),
            'removed': set(old_qs).difference(set(new_qs))
        }
        # if sets are the same
        if not diff['inserted'] and not diff['removed']:
            # if created and sets are the same,
            # entry has been filtered and can't be there
            to_python = model.id.field.to_python
            if to_python(instance_id) in new_qs:
                # changed and may have moved
                # just send new instance and pos
                send_change(sub, template, qs.get(pk=instance_id))
                # getting from qs to keep annotations

        # if sets aren't the same, then considering that only one entry
        # was added or has changed:
        # - it could have been removed if newly filtered (changed)
        # - it could have been added if no more filtered (changed)
        # - it could have been added if created and not filtered
        # - it cannot have just moved neither changed or the set
        #   would have been the same
        # - it could have been added while not created, replacing
        #   another entry because of filters, so created or not,
        #   we have to handle both added and removed entries
        else:
            # using loops for now but shouldn't be usefull as we
            # are handling only one entry, the queryset shouldn't
            # move by more that one in and/or one out
            for id in diff['removed']:
                send_remove(sub, template, qs.get(pk=id))
            for id in diff['inserted']:
                send_insert(sub, template, qs.get(pk=id))


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
    subscriptions = Subscription.objects.filter(
        publication__model_class=sender_name,
        publication__model_module=sender_mod
    )

    for sub in subscriptions:
        model = sub.publication.model
        template = model_templates[sub.subscriber.model_template]

        old_qs = sub.queryset

        # if instance not in queryset, no need to remove it
        # or update the queryset
        # else:
        to_python = model.id.field.to_python
        if to_python(instance_id) in old_qs:
            qs = sub.get_queryset()
            if not qs.query.can_filter():
                qs.query.clear_limits()

            new_qs = sub.queryset

            diff = {
                'inserted': set(new_qs).difference(set(old_qs)),
                'removed': set(old_qs).difference(set(new_qs))
            }

            for id in diff['removed']:
                # Should only be the deleted instance if it was in qs
                instance = model(id=instance_id)
                send_remove(sub, template, instance)
            for id in diff['inserted']:
                # May have been replace if limits were set
                send_insert(sub, template, qs.get(pk=id))
