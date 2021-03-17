'''
Defines the ryzom View class and the main index view
'''
from asgiref.sync import async_to_sync
from django import http

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
            ws_connect()

        return autoexec(JS(js_set_token, dict(token=client.token)))


class RegisterManager:
    def __init__(self, queryset):
        self.queryset = queryset

    def update(self, content):
        from channels.layers import get_channel_layer
        channel = get_channel_layer()
        for registration in self.queryset:
            content.id = registration.subscriber_id
            content.parent = registration.subscriber_parent
            channel_name = registration.client.channel
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
