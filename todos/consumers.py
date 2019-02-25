import importlib
import json

from channels.generic.websocket import JsonWebsocketConsumer
from channels.auth import get_user
from django.contrib.auth.models import User
from asgiref.sync import async_to_sync

from todos.models import Clients, Subscriptions


class Consumer(JsonWebsocketConsumer, object):
    def connect(self):
        self.accept()
        user = async_to_sync(get_user)(self.scope)
        Clients.objects.create(
                channel=self.channel_name,
                user=user if isinstance(user, User) else None
        )
        self.send(json.dumps({'type': 'Connected'}))

    def disconnect(self, close_code):
        # Note that in some rare cases (power loss, etc) disconnect may fail
        # to run; this naive example would leave zombie channel names around.
        print('Disconnect')
        Clients.objects.filter(channel=self.channel_name).delete()

    def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = None
        if not data.get('_id', None):
            return
        try:
            msg_type = data['type']
        except KeyError:
            self.send(json.dumps({
                '_id': data['_id'],
                'type': 'Error',
                'params': {
                    'name': 'Bad message',
                    'message': 'message type not found'
                }
            }))
            return

        if msg_type in ['subscribe', 'unsubscribe', 'method', 'geturl']:
            func = getattr(self, f'recv_{msg_type}', None)
            if func:
                try:
                    func(data)
                except KeyError as e:
                    print(e)
                    self.send(json.dumps({
                        '_id': data.get('_id'),
                        'type': 'Error',
                        'params': {
                            'name': 'Bad format',
                            'message': '"params" key not found'
                        }
                    }))
        else:
            self.send(json.dumps({
                '_id': data['_id'],
                'type': 'Error',
                'params': {
                    'name': 'Bad message type',
                    'message': f'{msg_type} not recognized'
                }
            }))

    def recv_geturl(self, data):
        base = importlib.import_module('.base', 'todos.components')
        data = {
            '_id': data['_id'],
            'type': 'Result',
            'params': base.Base().to_obj()
        }
        self.send(json.dumps(data))

    def recv_getcomponent(self, data):
        pass

    def insert_component(self, data, change=False):
        self.send(json.dumps({
            'type': 'DDP',
            'params': {
                'type': 'insert' if not change else 'change',
                'params': data['instance']
            }
        }))

    def remove_component(self, data):
        self.send(json.dumps({
            'type': 'DDP',
            'params': {
                'type': 'remove',
                'params': {
                    '_id': data['_id'],
                    'parent': data['parent']
                }
            }
        }))

    def handle_ddp(self, data):
        if data['params']['type'] == 'inserted':
            self.insert_component(data['params'])
        elif data['params']['type'] == 'changed':
            self.insert_component(data['params'], True)
        elif data['params']['type'] == 'removed':
            self.remove_component(data['params'])

    def recv_subscribe(self, data):
        params = data['params']
        to_send = {'_id': data['_id']}
        client = Clients.objects.get(channel=self.channel_name)
        for key in ['name', '_id', 'template']:
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
            sub = Subscriptions.objects.create(
                    name=params['name'],
                    parent=params['_id'],
                    template_module=params['template'][0],
                    template_class=params['template'][1],
                    client=client)
            to_send.update({
                'type': 'Result',
                'params': {
                    'name': params['name'],
                    'sub_id': sub.id
                }
            })
        self.send(json.dumps(to_send))

    def recv_unsubscribe(self, data):
        params = data['params']
        self.send(json.dumps({
            '_id': data['_id'],
            'type': 'unsubscribed',
            'message': 'Got unsub',
            'params': {
                'name': params['name']
            }
        }))
