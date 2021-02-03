'''
Functions to communicate DDP messages to the channel layer.
'''
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_insert(sub, model, tmpl, _id):
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
    :param int _id: The id of the model to insert
    '''
    if sub.client is None or not sub.client.channel:
        sub.delete()
        return

    tmpl_instance = tmpl(model.objects.get(id=_id))
    tmpl_instance.parent = sub.parent
    tmpl_instance.position = sub.queryset.index(_id)
    data = {
        'type': 'handle.ddp',
        'params': {
            'type': 'inserted',
            'instance': tmpl_instance.to_obj()
        }
    }
    channel = get_channel_layer()
    async_to_sync(channel.send)(sub.client.channel, data)


def send_change(sub, model, tmpl, _id):
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
    :param int _id: The id of the model to change
    '''
    tmpl_instance = tmpl(model.objects.get(id=_id))
    tmpl_instance.parent = sub.parent
    tmpl_instance.position = sub.queryset.index(_id)
    data = {
        'type': 'handle.ddp',
        'params': {
            'type': 'changed',
            'instance': tmpl_instance.to_obj()
        }
    }
    channel = get_channel_layer()
    async_to_sync(channel.send)(sub.client.channel, data)


def send_remove(sub, model, tmpl, _id):
    '''
    Send remove message.
    Function used to send a DDP message to a specific client
    via the channel layer.
    Uses the template class associated with a publication
    to create a new instance of a component attached to a
    model that was removed, in order to get the computed _id
    and send the computed _id to the client.
    Essentially called by post_save and post_delete signal handlers

    :param Subscriptions sub: The Subscription holding the connection \
            information
    :param Publishable model: The class of the model to remove
    :param Component tmpl: The component subclass that templates \
            the model instance
    :param int _id: The id of the model to remove
    '''
    if sub.client is None:
        if sub.id:
            sub.delete()
        return

    tmp = model()
    tmp.id = _id
    tmpl_instance = tmpl(tmp)
    data = {
        'type': 'handle.ddp',
        'params': {
            'type': 'removed',
            '_id': tmpl_instance._id,
            'parent': sub.parent
        }
    }
    channel = get_channel_layer()
    async_to_sync(channel.send)(sub.client.channel, data)
