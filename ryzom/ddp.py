from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_insert(sub, model, tmpl, _id):
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
