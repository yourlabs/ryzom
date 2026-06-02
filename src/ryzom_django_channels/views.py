'''
Defines the ryzom View class and the main index view
'''

import time
import importlib

from threading import Thread

from asgiref.sync import async_to_sync
from django import http
from django.conf import settings

from channels.layers import get_channel_layer
from ryzom.html import Meta
from ryzom_django_channels.models import (Client, Publication, Registration,
                                          Subscription)


def _transport():
    '''Which transport the client should use.

    ``RYZOM_TRANSPORT`` forces it ('ws' or 'poll'); otherwise push when channels
    is enabled, else client-pull polling. Set it to 'poll' to run the live UI
    where no server-initiated communication is allowed (see POLLING.md), even
    when the channels infra happens to be available.
    '''
    forced = getattr(settings, 'RYZOM_TRANSPORT', None)
    if forced:
        return forced
    return 'ws' if getattr(settings, 'CHANNELS_ENABLE', False) else 'poll'


class ReactiveMixin:
    def get_token(view):
        user = view.request.user
        try:
            client = Client.objects.create(user=user)
        except ValueError:
            client = Client.objects.create()

        view.client = client

        # Use a meta tag instead of inline script for CSP compliance. The
        # transport attrs tell ryzom.js whether to open a websocket (push) or
        # poll (client-pull); in poll mode it never constructs a WebSocket.
        return Meta(
            name='ryzom-config',
            content=client.token,
            **{
                'data-ws-host': settings.WS_HOST,
                'data-ws-port': settings.WS_PORT,
                'data-transport': _transport(),
                'data-poll-url': getattr(settings, 'POLL_URL', ''),
                'data-poll-interval': str(getattr(settings, 'POLL_INTERVAL', 2000)),
            }
        )


def ddp_poll(request):
    '''Client-pull endpoint: the polling transport's only server touchpoint.

    The client GETs this with its token on its own interval; we only ever
    respond (never push), satisfying the "client-initiated only" constraint.
    Authenticated by the token alone, exactly like the websocket consumer (hence
    no CSRF) — the token is the capability. Returns the pending DDP messages for
    the client to feed through ``handleDDP``, or ``{reload: true}`` when the
    client is unknown (swept / server restarted) and its DOM can't be repaired
    incrementally.
    '''
    from ryzom_django_channels.polling import poll_client, sweep_stale_clients

    token = request.GET.get('token') or request.POST.get('token') or ''
    client = Client.objects.filter(token=token).last()
    if client is None:
        resp = http.JsonResponse({'reload': True})
    else:
        sweep_stale_clients(getattr(settings, 'POLL_TTL', 60))
        resp = http.JsonResponse({'messages': poll_client(client)})
    resp['Cache-Control'] = 'no-store'
    return resp


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
        if channel_name:
            self.send(channel_name, content)
        else:
            self.defer(registration.client, content)

    def refresh(self, *args, **kwargs):
        for registration in self.queryset:
            content_module = importlib.import_module(registration.subscriber_module)
            content_class = getattr(content_module, registration.subscriber_class)
            self._replace(registration, content_class, *args, **kwargs)

    def send(self, channel_name, content):
        Thread(
            target=self._send,
            args=[channel_name, content]
        ).start()

    def _send(self, channel_name, content):
        channel = get_channel_layer()
        if channel_name:
            inner = content.to_obj()
            async_to_sync(channel.send)(channel_name, {
                'type': 'handle.ddp',
                'params': {
                    'type': 'changed',
                    'instance': inner
                }
            })

    def defer(self, client, content):
        Thread(
            target=self.wait,
            args=[client, content]
        ).start()

    def wait(self, client, content):
        for i in range(10):
            try:
                client.refresh_from_db()
            except client.__class__.DoesNotExist:
                break
            if client.channel:
                self._send(client.channel, content)
                break
            else:
                time.sleep(1)

    def delete(self):
        self.queryset.delete()


def register(register_name):
    queryset = Registration.objects.filter(name=register_name)
    return RegisterManager(queryset)
