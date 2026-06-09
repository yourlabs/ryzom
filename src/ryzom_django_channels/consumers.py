'''
Consumer for Django channels.
Handles websockets messages from client and channels layer
'''
import json

from asgiref.sync import async_to_sync
from channels.auth import get_user, login
from channels.generic.websocket import JsonWebsocketConsumer
from django.conf import settings
from django.utils import timezone


AUTH_BACKEND = settings.AUTHENTICATION_BACKENDS[0]

class Consumer(JsonWebsocketConsumer):
    '''
    Consumer class, inherited from the channels' JsonWebsocketConsumer
    '''

    def connect(self):
        from ryzom_django_channels.models import Client
        '''
        Websocket connect handler.
        This method tries to get the user connecting and re-attach (or reject)
        the ryzom.models.Client identified by the connection token, saving the
        channel name for future access from the channel layer.
        Sends back a 'Connected' or 'Reload' message (see reattach()).
        '''
        client = None
        user = async_to_sync(get_user)(self.scope)
        token = self.scope['query_string'].decode()
        if token:
            client = Client.objects.filter(token=token).last()
            if client and client.user:
                async_to_sync(login)(self.scope, client.user, backend=AUTH_BACKEND)
                self.scope['session'].save()

        self.accept()
        self.send(json.dumps({'type': self.reattach(client, user)}))

    def reattach(self, client, user):
        '''
        Re-bind a (possibly reconnecting) client to this channel and decide
        whether the browser can resume seamlessly or must reload.

        Returns the message type to send back:
        - 'Connected' when the client is known and its DOM is still valid
          (subscriptions intact, nothing was pushed while it was detached) so
          ryzom.js just resumes live updates;
        - 'Reload' when the client is unknown/expired (reaped after the grace
          period or a first-ever connect), data drifted while it was detached
          (needs_resync), or the previous connection died uncleanly (stale
          channel, see below), so the DOM must be rebuilt.

        Clears the detached/resync state on a known client. Its
        Subscriptions/Registrations were kept alive across the disconnect (see
        disconnect()), so we only reload when data drifted while detached.

        Race-safe against a concurrent _mark_needs_resync() (a worker pushing a
        change as the client reconnects): we re-attach the channel first, then
        atomically test-and-clear needs_resync. A racing push then either lands
        on the now-live channel or sets the flag where phase 2 still observes
        it — it can neither be lost nor clobbered.
        '''
        from ryzom_django_channels.models import Client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if client is None:
            return 'Reload'
        # A non-empty stored channel means the previous connection never ran
        # disconnect() (process SIGKILL/crash, or a network partition that the
        # old socket hasn't timed out yet). In that window pushes went to
        # a dead channel and were silently dropped *without* setting
        # needs_resync, so the DOM may have drifted: force one reload. A clean
        # blip always clears the channel in disconnect(), so the common
        # seamless path (channel == '') is unaffected.
        stale = bool(client.channel)
        # Phase 1: re-attach (adopt the authed user if the client had none).
        fields = {'channel': self.channel_name, 'detached_at': None}
        if not client.user and isinstance(user, User):
            fields['user'] = user
        Client.objects.filter(pk=client.pk).update(**fields)
        # Phase 2: atomic test-and-clear. .update() returns the rows it changed
        # (1 iff needs_resync was set), so we only clear a flag we observed.
        resync = Client.objects.filter(
            pk=client.pk, needs_resync=True).update(needs_resync=False)
        return 'Reload' if (stale or resync) else 'Connected'

    def disconnect(self, close_code):
        from ryzom_django_channels.models import Client
        '''
        Websocket disconnect handler.
        A disconnect is almost always transient (redeploy, Daphne restart,
        network blip). Rather than delete the Client (which would cascade
        its Subscriptions/Registrations and force a full reload on reconnect),
        mark it detached and keep its bindings so a same-token reconnect can
        re-attach and resume live updates. Genuinely-gone tabs are removed by
        the grace-period reaper below.
        '''
        Client.objects.filter(channel=self.channel_name).update(
            channel='', detached_at=timezone.now())

        # Reap genuinely-gone clients (grace-expired detached ws clients +
        # never-attached zombies). We don't clear_queue here: the poll queue is
        # keyed by token, TTL'd, and a detached ws client may reconnect at once
        # (poll clients never reach this ws disconnect anyway). Quiet systems
        # can also schedule the `reap_ryzom_clients` command (same logic).
        Client.reap_stale()

    def receive(self, text_data):
        from ryzom_django_channels.models import Client
        '''
        Websocket message handler.
        Dispatches message to type specific subhandlers after some
        error checking on the message format.
        Known message type: 'ping'.
        A message should have:
        - an 'id' key, which is used to find the right
        callback function the client defined
        - a 'type' key, one of the known message types described above
        - a 'params' key, which is used as a parameter, specific to
        each message type.
        '''
        if not Client.objects.filter(channel=self.channel_name).count():
            self.send(json.dumps({'type': 'Reload'}))
            return

        data = json.loads(text_data)
        msg_type = None
        if not data.get('id', None):
            return
        try:
            msg_type = data['type']
        except KeyError:
            self.send(json.dumps({
                'id': data['id'],
                'type': 'Error',
                'params': {
                    'name': 'Bad message',
                    'message': 'message type not found'
                }
            }))
            return

        if msg_type in ['ping']:
            func = getattr(self, f'recv_{msg_type}', None)
            if func:
                if data.get('params', None) is None:
                    self.send(json.dumps({
                        'id': data.get('id'),
                        'type': 'Error',
                        'params': {
                            'name': 'Bad format',
                            'message': '"params" key not found'
                        }
                    }))
                else:
                    func(data)
        else:
            self.send(json.dumps({
                'id': data['id'],
                'type': 'Error',
                'params': {
                    'name': 'Bad message type',
                    'message': f'{msg_type} not recognized'
                }
            }))

    def recv_ping(self, data):
        self.send(json.dumps({
            'id': data['id'],
            'type': 'pong'
        }))

    def insert_component(self, data, change=False):
        '''
        This method is meant to be called by the DDP dispacher.
        It send a DDP insert/change message to the client with
        a serialized component as params
        '''
        self.send(json.dumps({
            'type': 'DDP',
            'params': {
                'type': 'insert' if not change else 'change',
                'params': data['instance']
            }
        }))

    def remove_component(self, data):
        '''
        This method is meant to be called by the DDP dispacher.
        It send a DDP remove message to the client with the parent
        and id of the component to remove as params
        '''
        self.send(json.dumps({
            'type': 'DDP',
            'params': {
                'type': 'remove',
                'params': {
                    'id': data['id'],
                    'parent': data['parent']
                }
            }
        }))

    def handle_ddp(self, data):
        '''
        DDP dispacher.
        handler for 'handle.ddp' messages sent over the channel layer.
        dispaches the message to the above two methods
        '''
        if data['params']['type'] == 'inserted':
            self.insert_component(data['params'])
        elif data['params']['type'] == 'changed':
            self.insert_component(data['params'], True)
        elif data['params']['type'] == 'removed':
            self.remove_component(data['params'])

