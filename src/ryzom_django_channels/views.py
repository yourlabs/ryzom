'''
Defines the ryzom View class and the main index view
'''
import importlib

from asgiref.sync import async_to_sync
from django import http
from django.conf import settings

from py2js.renderer import JS, autoexec
from ryzom.components import Component
from ryzom_django_channels.models import (Client, Publication, Registration,
                                          Subscription)


class ReactiveMixin:
    def get_token(view):
        user = view.request.user
        try:
            client = Client.objects.create(user=user)
        except ValueError:
            client = Client.objects.create()

        view.client = client

        def js_set_token():
            window.token = token
            window.ws_host = host
            window.ws_port = port
            ws_connect()

        return autoexec(JS(js_set_token, dict(
            token=client.token,
            host=settings.WS_HOST,
            port=settings.WS_PORT,
        )))


class RegisterManager:
    def __init__(self, queryset):
        self.queryset = queryset

    def replace(self, content_class, *args, **kwargs):
        for registration in self.queryset:
            registration.subscriber_class = content_class.__name__
            registration.subscriber_module = content_class.__module__
            registration.save()

            self._replace(registration, content_class, *args, **kwargs)

    def _replace(self, registration, content_class, *args, **kwargs):
        user = registration.client.user
        content = content_class(*args, user=user, **kwargs)
        content.id = registration.subscriber_id
        content.parent = registration.subscriber_parent
        channel_name = registration.client.channel
        self.send(channel_name, content)

    def refresh(self, *args, **kwargs):
        for registration in self.queryset:
            content_module = importlib.import_module(registration.subscriber_module)
            content_class = getattr(content_module, registration.subscriber_class)
            self._replace(registration, content_class, *args, **kwargs)

    def send(self, channel_name, content):
        from channels.layers import get_channel_layer
        channel = get_channel_layer()
        if channel_name:
            async_to_sync(channel.send)(channel_name, {
                'type': 'handle.ddp',
                'params': {
                    'type': 'changed',
                    'instance': content.to_obj()
                }
            })


def register(register_name):
    queryset = Registration.objects.filter(name=register_name)
    return RegisterManager(queryset)
