import importlib

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class Clients(models.Model):
    channel = models.CharField(max_length=255)
    user = models.ForeignKey(
                User,
                models.SET_NULL,
                blank=True,
                null=True
           )


class Subscriptions(models.Model):
    name = models.CharField(max_length=255)
    parent = models.CharField(max_length=255)
    template_module = models.CharField(max_length=255)
    template_class = models.CharField(max_length=255)
    client = models.ForeignKey(Clients, models.CASCADE)


class Tasks(models.Model):
    user = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)
    about = models.CharField(max_length=1024)


@receiver(post_save, sender=Tasks)
def ddp_insert_change(sender, **kwargs):
    created = kwargs.pop('created')
    instance = kwargs.pop('instance')
    data = {
        'type': 'handle.ddp',
        'params': {
            'type': 'inserted' if created else 'changed',
        }
    }
    subs = Subscriptions.objects.filter(name='tasks')
    for sub in subs:
        mfile, mpath = sub.template_module[::-1].split('.', 1)
        tmpl_module = importlib.import_module(f'.{mfile[::-1]}', mpath[::-1])
        tmpl_class = getattr(tmpl_module, sub.template_class)
        tmpl_instance = tmpl_class(instance)
        tmpl_instance.parent = sub.parent
        data['params']['instance'] = tmpl_instance.to_obj()
        client = sub.client
        channel = get_channel_layer()
        async_to_sync(channel.send)(client.channel, data)


@receiver(post_delete, sender=Tasks)
def ddp_delete(sender, **kwargs):
    instance = kwargs.pop('instance')
    data = {
        'type': 'handle.ddp',
        'params': {
            'type': 'removed',
        }
    }
    subs = Subscriptions.objects.filter(name='tasks')
    for sub in subs:
        mfile, mpath = sub.template_module[::-1].split('.', 1)
        tmpl_module = importlib.import_module(f'.{mfile[::-1]}', mpath[::-1])
        tmpl_class = getattr(tmpl_module, sub.template_class)
        tmpl_instance = tmpl_class(instance)
        data['params']['parent'] = sub.parent
        data['params']['_id'] = tmpl_instance._id
        client = sub.client
        channel = get_channel_layer()
        async_to_sync(channel.send)(client.channel, data)
