'''
Functions to communicate DDP messages to the client.

Two transports share one serialization:

- **push** (websocket): ``send_insert``/``send_change``/``send_remove`` wrap a
  rendered row in the channel-layer envelope (``handle.ddp`` /
  ``inserted``/``changed``/``removed``) and write it to the client's channel.
  The consumer then unwraps it into the client message below.
- **pull** (polling, see ``POLLING.md``): ``client_message`` builds that same
  client message directly — ``{type: insert|change|remove, params}`` — for a
  poll response, skipping the channel layer entirely. Both paths render the row
  identically via the helpers below, so a polled DOM is byte-identical to a
  pushed one.
'''
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def _row_obj(sub, tmpl, instance):
    '''Serialize a row component positioned within the subscription's window.

    ``parent`` is the subscribed container's id and ``position`` is the row's
    index in the subscription's freshly persisted window, so the client inserts
    it at the right child index. Shared by insert and change (a change ships the
    full re-rendered row).
    '''
    tmpl_instance = tmpl(instance)
    tmpl_instance.parent = sub.subscriber_id
    tmpl_instance.position = sub.queryset.index(instance.pk)
    return tmpl_instance.to_obj()


def _remove_ref(sub, tmpl, instance):
    '''The ``{id, parent}`` a remove needs: just the component's DOM id (read
    off a throwaway template instance) and the subscribed container's id.'''
    return {'id': tmpl(instance).id, 'parent': sub.subscriber_id}


def client_message(sub, tmpl, kind, instance):
    '''The DDP message a polling client applies via ``ryzom.js:handleDDP``.

    ``kind`` is ``'insert' | 'change' | 'remove'`` (as yielded by
    ``signals.iter_window_ops``). Returns ``{'type': kind, 'params': ...}`` —
    the exact shape the consumer hands to ``handleDDP`` on the push path — so
    the poll response is just a list of these.
    '''
    if kind == 'remove':
        return {'type': 'remove', 'params': _remove_ref(sub, tmpl, instance)}
    return {'type': kind, 'params': _row_obj(sub, tmpl, instance)}


def _send_to_channel(sub, params):
    channel = get_channel_layer()
    async_to_sync(channel.send)(sub.client.channel, params)


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
    if sub.client is None or sub.client.channel == '':
        return

    _send_to_channel(sub, {
        'type': 'handle.ddp',
        'params': {
            'type': 'inserted',
            'instance': _row_obj(sub, tmpl, instance),
        },
    })


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
    if sub.client is None or sub.client.channel == '':
        return

    _send_to_channel(sub, {
        'type': 'handle.ddp',
        'params': {
            'type': 'changed',
            'instance': _row_obj(sub, tmpl, instance),
        },
    })


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

    ``instance`` should be the real, live model instance whenever it still
    exists (e.g. a row filtered out of a subscription): only on a genuine
    delete, where the row is gone from the DB, is a bare ``model(pk=...)``
    shell passed — and then only the template's DOM id is read off it.

    :param Subscriptions sub: The Subscription holding the connection \
            information
    :param Publishable model: The class of the model to remove
    :param Component tmpl: The component subclass that templates \
            the model instance
    :param int id: The id of the model to remove
    '''
    if sub.client is None or sub.client.channel == '':
        return

    ref = _remove_ref(sub, tmpl, instance)
    _send_to_channel(sub, {
        'type': 'handle.ddp',
        'params': {
            'type': 'removed',
            'id': ref['id'],
            'parent': ref['parent'],
        },
    })
