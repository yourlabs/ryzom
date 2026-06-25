'''
Defines the ryzom View class and the main index view
'''

import json
import secrets
import time
import importlib

from threading import Thread

from asgiref.sync import async_to_sync
from django import http
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

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
        # A GET must stay a safe method (RFC 7231/9110): it must not write, and
        # a JS-less crawler (e.g. GoogleBot) must not mint Client/Subscription
        # rows. So build a *transient* Client carrying a fresh capability token
        # and the request user, but do NOT save it. The row — and any
        # Subscription/Registration — is created later, when the client actually
        # contacts the server over its transport: the websocket consumer's
        # connect()/recv_subscribe, or the first poll POST. See PROBLEM.md.
        user = view.request.user
        if not getattr(user, 'is_authenticated', False):
            user = None
        view.client = Client(token=secrets.token_urlsafe(), user=user)

        # Use a meta tag instead of inline script for CSP compliance. The
        # transport attrs tell ryzom.js whether to open a websocket (push) or
        # poll (client-pull); in poll mode it never constructs a WebSocket.
        return Meta(
            name='ryzom-config',
            content=view.client.token,
            **{
                'data-ws-host': settings.WS_HOST,
                'data-ws-port': settings.WS_PORT,
                'data-transport': _transport(),
                'data-poll-url': getattr(settings, 'POLL_URL', ''),
                'data-poll-interval': str(getattr(settings, 'POLL_INTERVAL', 2000)),
            }
        )


@csrf_exempt
def ddp_poll(request):
    '''Client-pull endpoint: the polling transport's only server touchpoint.

    The client's *first* poll is a POST carrying its subscribe/register
    descriptors: that is when the Client and its Subscriptions are created (a
    POST, so the write is RFC-safe — the page GET deliberately created nothing,
    see ``ReactiveMixin.get_token``). Subsequent polls are GETs that only ever
    *respond* (never push), satisfying the "client-initiated only" constraint.
    Authenticated by the token alone, like the websocket consumer (hence no
    CSRF) — the token is the capability. Returns the pending DDP messages for
    the client to feed through ``handleDDP``, or ``{reload: true}`` when the
    client is unknown (swept / server restarted) and its DOM can't be repaired
    incrementally.
    '''
    from ryzom_django_channels.polling import (establish, poll_client,
                                               sweep_stale_clients)

    token = request.GET.get('token') or request.POST.get('token') or ''
    client = Client.objects.filter(token=token).last()

    if request.method == 'POST' and token:
        try:
            descriptors = json.loads(request.body or b'{}')
        except (ValueError, TypeError):
            descriptors = {}
        if client is None:
            user = request.user if request.user.is_authenticated else None
            client, _ = Client.objects.get_or_create(
                token=token,
                defaults={'user': user, 'last_seen': timezone.now()},
            )
        establish(client, descriptors)

    if client is None:
        resp = http.JsonResponse({'reload': True})
    else:
        # Throttled internally so it hits the DB at most once per TTL window
        # rather than on every poll (see sweep_stale_clients).
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
