'''
Redis-backed message queue for HTTP polling transport.

Uses the same Redis instance configured in CHANNEL_LAYERS to avoid
adding a new dependency. Messages are stored per-client token with
a 10-minute TTL.
'''
import json

from ryzom_django_channels.redis_conn import get_redis as _get_redis


QUEUE_PREFIX = 'ryzom:poll:'
QUEUE_TTL = 600  # 10 minutes


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
