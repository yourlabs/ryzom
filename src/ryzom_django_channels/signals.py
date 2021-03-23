'''
Defines the django signals handlers.
'''
import importlib

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ryzom_django_channels.components import model_templates
from ryzom_django_channels.ddp import send_change, send_insert, send_remove
from ryzom_django_channels.models import Publication, Subscription
from ryzom_django_channels.pubsub import Publishable


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

    created = kwargs.pop('created')
    instance = kwargs.pop('instance')

    subscriptions = Subscription.objects.filter(
        publication__model_class=sender.__name__,
        publication__model_module=sender.__module__)

    for sub in subscriptions:
        template = model_templates[sub.subscriber.model_template]
        old_qs = sub.queryset

        sub.get_queryset()
        new_qs = sub.queryset

        diff = {
            'inserted': set(new_qs).difference(set(old_qs)),
            'removed': set(old_qs).difference(set(new_qs))
        }
        # if sets are the same
        if not diff['inserted'] and not diff['removed']:
            # if created and sets are the same,
            # entry has been filtered and can't be there
            if not created:
                # changed and may have moved
                # just send new instance and pos
                send_change(sub, sender, template, instance.id)

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
                send_remove(sub, sender, template, id)
            for id in diff['inserted']:
                send_insert(sub, sender, template, id)


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

    instance = kwargs.pop('instance')
    subscriptions = Subscription.objects.filter(
        publication__model_class=sender.__name__,
        publication__model_module=sender.__module__)

    for sub in subscriptions:
        template = model_templates[sub.subscriber.model_template]

        old_qs = sub.queryset

        # if instance not in queryset, no need to remove it
        # or update the queryset
        # else:
        if instance.id in old_qs:
            sub.get_queryset()
            new_qs = sub.queryset

            diff = {
                'inserted': set(new_qs).difference(set(old_qs)),
                'removed': set(old_qs).difference(set(new_qs))
            }

            for id in diff['removed']:
                send_remove(sub, sender, template, id)
            for id in diff['inserted']:
                send_insert(sub, sender, template, id)
