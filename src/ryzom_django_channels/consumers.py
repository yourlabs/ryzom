'''
Consumer for Django channels.
Handles websockets messages from client and channels layer
ddp_urlpattern and server_methods are subject to change in a
near future. Both will be handled in a separate file
'''
import importlib
import json
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.auth import get_user, login
from channels.generic.websocket import JsonWebsocketConsumer
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone

from ryzom_django_channels.methods import Methods
from ryzom_django_channels.models import Client, Publication, Subscription


class Consumer(JsonWebsocketConsumer):
    '''
    Consumer class, inherited from the channels' JsonWebsocketConsumer
    '''
    ddp_urlpatterns = importlib.import_module(
        settings.WS_URLPATTERNS).urlpatterns

    '''
    Import all user defined server methods
    '''
    for module in settings.SERVER_METHODS:
        importlib.import_module(module)

    def connect(self):
        '''
        Websocket connect handler.
        This method tries to get the user connecting and create a new
        ryzom.models.Client in DB, saving the channel name for future
        access from the channel layer.
        sends back a 'Connected' message to the client
        '''
        client = None
        user = async_to_sync(get_user)(self.scope)
        token = self.scope['query_string'].decode()
        if token:
            client = Client.objects.filter(token=token).last()
            if client and client.user:
                async_to_sync(login)(self.scope, client.user)
                self.scope['session'].save()

        self.accept()
        if client and client.channel != self.channel_name:
            client.channel = self.channel_name
            client.user = user if isinstance(user, User) else None
            client.save()
            self.send(json.dumps({'type': 'Connected'}))
        else:
            self.send(json.dumps({'type': 'Reload'}))

    def disconnect(self, close_code):
        '''
        Websocket disconnect handler.
        Removes the ryzom.models.Client entry attached to this
        channel, cascading deletion to Suscriptions
        Zombies that may stay in our DB on server reboots are removed in
        the ryzom.apps Appconfig.ready() function
        '''
        client = Client.objects.filter(channel=self.channel_name)
        if client.count():
            client.delete()

        expiration = timezone.now() - timedelta(minutes=2)
        deadclients = Client.objects.filter(channel='', created__lt=expiration)
        deadclients.delete()

    def receive(self, text_data):
        '''
        Websocket message handler.
        Dispatches message to type specific subhandlers after some
        error checking on the message format
        Known message types are 'subscribe', 'unsubscribe', 'method'
        and 'geturl'.
        In a near future, login and logout could be handled too,
        unless we use another way to do it, by method call or anything else
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

        if msg_type in [
                'subscribe', 'unsubscribe',
                'method', 'geturl',
                'login', 'logout', 'ping']:
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

    def recv_login(self, data):
        credentials = data['params']
        user = authenticate(**credentials)
        if user:
            async_to_sync(login)(self.scope, user)
            self.scope['session'].save()
            client = Client.objects.get(channel=self.channel_name)
            client.user = user
            client.save()
            self.send(json.dumps({
                'id': data['id'],
                'type': 'Success',
                'params': {
                    'token': f'{client.token}'
                }
            }))
        else:
            self.send(json.dumps({
                'id': data['id'],
                'type': 'Error',
                'params': {
                    'name': 'Credentials mismatch',
                    'message': 'Wrong username/password combination'
                }
            }))

    def recv_logout(self, data):
        pass

    def recv_geturl(self, data):
        '''
        geturl message handler.
        Creates a new ryzom.views.View based on ddp_urlpattern configuration
        and attach it to this consumer instance.
        Renders the view then send it to the client
        If a view as already been created, destroy it and creates the new one
        view's callback (oncreate, ondestroy) are called here
        '''
        to_url = data['params'].get('url', '/')
        to_query = data['params'].get('query', '')
        for url in Consumer.ddp_urlpatterns:
            if url.pattern.match(to_url):
                cview = getattr(self, 'view', None)
                if not cview or not isinstance(cview, url.callback):
                    if cview:
                        cview.ondestroy()
                    client = Client.objects.filter(channel=self.channel_name).last()
                    req = Request(client, url.callback)
                    cview = self.view = url.callback(req)
                    cview.oncreate(to_url)
                if (cview.onurl(to_url)):
                    self.send(json.dumps({
                        'id': data['id'],
                        'type': 'Success',
                        'params': []
                    }))
                else:
                    data = {
                        'id': data['id'],
                        'type': 'Error',
                        'params': ''
                    }
                    self.send(json.dumps(data))
                break

    def recv_method(self, data):
        '''
        method message handler.
        Lookup methods then call them with the 'params' key as parameter.
        Methods writers should handle that params.
        Methods should return a value that evaluates to True on Success.
        Methods return value should be serializable, it will be sent
        to the client as parameter for the callback
        '''
        to_send = {'id': data['id']}
        params = data['params']
        method = Methods.get(params['name'])
        if method is None:
            to_send.update({
                'type': 'Error',
                'params': {
                    'name': 'Not found',
                    'message': f'Method {params["name"]} not found'
                }
            })
        else:
            user = async_to_sync(get_user)(self.scope)
            ret = method(user, params['params'])
            if ret:
                to_send.update({
                    'type': 'Success',
                    'params': ret
                })
            else:
                to_send.update({
                    'type': 'Error',
                    'params': ret
                })
        self.send(json.dumps(to_send))

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

    def recv_subscribe(self, data):
        '''
        subscribe message handler.
        Creates a new subscription for the current Client.
        'subscribe' params should contain:
        - an 'id' key, which refer to the component that asks for
        a subscription
        - a 'name' key, corresponding to the name of the publication
        this subscription is about
        '''
        params = data['params']
        to_send = {'id': data['id']}
        client = Client.objects.get(channel=self.channel_name)
        print(f'GOT SUBSCRIBE FOR CLIENT {client}')
        for key in ['name', 'sub_id']:
            if key not in params:
                to_send.update({
                    'type': 'Error',
                    'params': {
                        'name': 'Bad format',
                        'message': f'Subscription {key} not found'
                    }
                })
                self.send(json.dumps(to_send))
                return
        if not client:
            to_send.update({
                'type': 'Error',
                'params': {
                    'name': 'Client not found',
                    'message': 'No client was found for this channel name'
                }
            })
        else:
            pub = Publication.objects.get(name=params['name'])
            sub = Subscription.objects.filter(
                publication=pub,
                parent=params['parent_id'],
                client=client).first()
            if not sub:
                sub = Subscription(
                        publication=pub,
                        parent=params['parent_id'],
                        client=client)
                sub.save()
            else:
                print('SUBSCRIPTION FOUND')
                sub.exec_query(params['opts'])
            print(sub.client, sub)

            to_send.update({
                'type': 'Success',
                'params': {
                    'name': params['name'],
                    'sub_id': f"{sub.id}",
                    'length': len(sub.queryset)
                }
            })
        self.send(json.dumps(to_send))

    def recv_unsubscribe(self, data):
        '''
        unsubscribe message handler.
        not implemented yes but meant to delete the subscription
        attached to the current Client/Publication name from DB
        '''
        params = data['params']
        self.send(json.dumps({
            'id': data['id'],
            'type': 'unsubscribed',
            'message': 'Got unsub',
            'params': {
                'name': params['name']
            }
        }))
