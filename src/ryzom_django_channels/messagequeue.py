'''
Redis-backed message queue for HTTP polling transport.

Uses the same Redis instance configured in CHANNEL_LAYERS to avoid
adding a new dependency. Messages are stored per-client token with
a 10-minute TTL.
'''
import json

from django.conf import settings


QUEUE_PREFIX = 'ryzom:poll:'
QUEUE_TTL = 600  # 10 minutes


def _get_redis():
    '''Get a Redis connection from CHANNEL_LAYERS config.'''
    config = settings.CHANNEL_LAYERS['default']['CONFIG']
    host_config = config['hosts'][0]

    import redis
    if isinstance(host_config, str):
        return redis.Redis.from_url(host_config)
    elif isinstance(host_config, (list, tuple)):
        return redis.Redis(host=host_config[0], port=host_config[1])
    elif isinstance(host_config, dict):
        return redis.Redis(**host_config)
    return redis.Redis()


def _queue_key(client_token):
    return f'{QUEUE_PREFIX}{client_token}'


def push_message(client_token, message_dict):
    '''Push a message to the client's polling queue.'''
    r = _get_redis()
    key = _queue_key(client_token)
    r.rpush(key, json.dumps(message_dict))
    r.expire(key, QUEUE_TTL)


def drain_messages(client_token):
    '''Atomically drain all messages from the client's queue.'''
    r = _get_redis()
    key = _queue_key(client_token)
    pipe = r.pipeline()
    pipe.lrange(key, 0, -1)
    pipe.delete(key)
    results = pipe.execute()
    return [json.loads(msg) for msg in results[0]]


def clear_queue(client_token):
    '''Delete the client's polling queue.'''
    r = _get_redis()
    r.delete(_queue_key(client_token))
