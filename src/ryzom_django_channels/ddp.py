'''
Functions to communicate DDP messages to the channel layer.
'''
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from ryzom_django_channels.messagequeue import push_message


def _client_is_available(client):
    '''Check if a client is reachable via its transport.'''
    if client is None:
        return False
    if client.transport == 'poll':
        return True
    return client.channel != ''


def _translate_ddp(handle_ddp_params):
    '''
    Translate handle.ddp params into the DDP format the JS client expects.

    The Consumer's handle_ddp method does this translation for WS clients;
    for poll clients we do it here before pushing to Redis.

    Translation map:
    - inserted → {type: 'insert', params: instance}
    - changed  → {type: 'change', params: instance}
    - removed  → {type: 'remove', params: {id: ..., parent: ...}}
    '''
    ddp_type = handle_ddp_params['type']
    if ddp_type == 'inserted':
        return {
            'type': 'DDP',
            'params': {
                'type': 'insert',
                'params': handle_ddp_params['instance'],
            },
        }
    elif ddp_type == 'changed':
        return {
            'type': 'DDP',
            'params': {
                'type': 'change',
                'params': handle_ddp_params['instance'],
            },
        }
    elif ddp_type == 'removed':
        return {
            'type': 'DDP',
            'params': {
                'type': 'remove',
                'params': {
                    'id': handle_ddp_params['id'],
                    'parent': handle_ddp_params['parent'],
                },
            },
        }
    return None


def _send_to_client(client, data):
    '''
    Send a handle.ddp message to a client via the appropriate transport.

    For WebSocket clients: send through the channel layer as before.
    For poll clients: translate to DDP format and push to Redis queue.
    '''
    if client.transport == 'poll':
        msg = _translate_ddp(data['params'])
        if msg:
            push_message(client.token, msg)
    else:
        channel = get_channel_layer()
        async_to_sync(channel.send)(client.channel, data)


def send_insert(sub, tmpl, instance):
    '''
    Send insert message.
    Function used to send a DDP message to a specific client
    via the channel layer.
    Uses the template class associated with a publication
    to create a new instance of a component attached to a
    model that was inserted, updated or removed
    Essentially called by post_save and post_delete signal handlers

    :param Subscriptions sub: The Subscription holding the connection \
            information
    :param Publishable model: The class of the model to insert
    :param Component tmpl: The component subclass that templates \
            the model instance
    :param int id: The id of the model to insert
    '''
    if not _client_is_available(sub.client):
        return

    tmpl_instance = tmpl(instance)
    tmpl_instance.parent = sub.subscriber_id
    tmpl_instance.position = sub.queryset.index(instance.pk)
    data = {
        'type': 'handle.ddp',
        'params': {
            'type': 'inserted',
            'instance': tmpl_instance.to_obj()
        }
    }
    _send_to_client(sub.client, data)


def send_change(sub, tmpl, instance):
    '''
    Send change message.
    Function used to send a DDP message to a specific client
    via the channel layer.
    Uses the template class associated with a publication
    to create a new instance of a component attached to a
    model that was updated
    Essentially called by post_save and post_delete signal handlers

    :param Subscriptions sub: The Subscription holding the connection \
            information
    :param Publishable model: The class of the model to change
    :param Component tmpl: The component subclass that templates \
            the model instance
    :param int id: The id of the model to change
    '''
    if not _client_is_available(sub.client):
        return

    tmpl_instance = tmpl(instance)
    tmpl_instance.parent = sub.subscriber_id
    tmpl_instance.position = sub.queryset.index(instance.pk)
    data = {
        'type': 'handle.ddp',
        'params': {
            'type': 'changed',
            'instance': tmpl_instance.to_obj()
        }
    }
    _send_to_client(sub.client, data)


def send_remove(sub, tmpl, instance):
    '''
    Send remove message.
    Function used to send a DDP message to a specific client
    via the channel layer.
    Uses the template class associated with a publication
    to create a new instance of a component attached to a
    model that was removed, in order to get the computed id
    and send the computed id to the client.
    Essentially called by post_save and post_delete signal handlers

    :param Subscriptions sub: The Subscription holding the connection \
            information
    :param Publishable model: The class of the model to remove
    :param Component tmpl: The component subclass that templates \
            the model instance
    :param int id: The id of the model to remove
    '''
    if not _client_is_available(sub.client):
        return

    tmpl_instance = tmpl(instance)
    data = {
        'type': 'handle.ddp',
        'params': {
            'type': 'removed',
            'id': tmpl_instance.id,
            'parent': sub.subscriber_id
        }
    }
    _send_to_client(sub.client, data)
