'''
Defines the ryzom View class and the main index view
'''

import logging
import importlib

from asgiref.sync import async_to_sync
from django import http
from django.conf import settings

from channels.layers import get_channel_layer
from ryzom.html import Meta
from ryzom_django_channels.messagequeue import push_message
from ryzom_django_channels.models import (Client, Publication, Registration,
                                          Subscription)

logger = logging.getLogger(__name__)


class ReactiveMixin:
    def get_token(view):
        user = view.request.user
        try:
            client = Client.objects.create(user=user)
        except ValueError:
            client = Client.objects.create()

        transport = getattr(settings, 'RYZOM_TRANSPORT', 'auto')
        poll_url = getattr(settings, 'RYZOM_POLL_URL', '/ddp/')

        if transport == 'poll':
            client.transport = 'poll'
            client.save()

        view.client = client

        # Use a meta tag instead of inline script for CSP compliance
        return Meta(
            name='ryzom-config',
            content=client.token,
            **{
                'data-ws-host': settings.WS_HOST,
                'data-ws-port': settings.WS_PORT,
                'data-transport': transport,
                'data-poll-url': poll_url,
            }
        )


class RegisterManager:
    def __init__(self, queryset):
        self.queryset = queryset

    def replace(self, content_class, *args, **kwargs):
        for registration in self.queryset:
            # One bad registration (stale client, template that raises for
            # this user...) must not silence the refresh for everyone else.
            try:
                registration.subscriber_class = content_class.__name__
                registration.subscriber_module = content_class.__module__
                registration.save()

                self._replace(registration, content_class, *args, **kwargs)
            except Exception:
                logger.exception(
                    'ryzom: replace failed for registration %s (%s)',
                    registration.pk, registration.name)

    def _replace(self, registration, content_class, *args, **kwargs):
        client = registration.client
        if client is None:
            return
        content = content_class(*args, user=client.user, **kwargs)
        content.id = registration.subscriber_id
        content.parent = registration.subscriber_parent

        if client.transport == 'poll':
            self._send_poll(client, content)
        else:
            channel_name = client.channel
            if channel_name:
                self.send(channel_name, content)
            else:
                # Detached ws client: flag a resync and drop the push. On
                # reconnect within grace, reattach() sees needs_resync and
                # returns 'Reload', so the browser rebuilds the whole page
                # with fresh state. (We used to spawn a thread that polled
                # for a quick reconnect and pushed this content to the
                # revived channel — but that reload then immediately wiped
                # the pushed DOM, making the thread pure waste; on a redeploy
                # the per-registration thread burst could also exhaust the DB
                # connection pool.)
                from ryzom_django_channels.ddp import _mark_needs_resync
                _mark_needs_resync(client)

    def refresh(self, *args, **kwargs):
        for registration in self.queryset:
            # Same isolation as replace(): a single failing registration
            # must not abort the refresh of the other clients.
            try:
                content_module = importlib.import_module(registration.subscriber_module)
                content_class = getattr(content_module, registration.subscriber_class)
                self._replace(registration, content_class, *args, **kwargs)
            except Exception:
                logger.exception(
                    'ryzom: refresh failed for registration %s (%s)',
                    registration.pk, registration.name)

    def send(self, channel_name, content):
        # Send synchronously (like ddp._send_to_client for model changes).
        # The previous Thread+async_to_sync wrapper silently failed when
        # refresh() was called from a Celery worker (the daemon thread tore
        # down before/while async_to_sync ran), so reactive refreshes
        # triggered by background tasks (contest creation, tally completion)
        # never reached the client. A direct async_to_sync(channel.send) is
        # fast and works from both request and worker contexts.
        self._send(channel_name, content)

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

    def _send_poll(self, client, content):
        '''Send a DDP change message to a poll client via Redis queue.'''
        inner = content.to_obj()
        msg = {
            'type': 'DDP',
            'params': {
                'type': 'change',
                'params': inner,
            },
        }
        push_message(client.token, msg)

    def delete(self):
        self.queryset.delete()


def register(register_name):
    queryset = Registration.objects.filter(
        name=register_name,
    ).select_related('client', 'client__user')
    return RegisterManager(queryset)
