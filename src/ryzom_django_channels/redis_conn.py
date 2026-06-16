'''
Shared, cached Redis connection for ryzom's queues and locks.

Both locks.py and messagequeue.py used to build a brand-new Redis client
(and thus a new TCP connection) on every call — including once per
post_save/post_delete of every Publishable model. A redis.Redis instance
wraps a thread-safe connection pool, so a single module-level instance is
the correct pattern; this module holds it.

Uses the same Redis instance configured in CHANNEL_LAYERS to avoid adding
a new dependency or setting.
'''
from django.conf import settings


_client = None


def get_redis():
    global _client
    if _client is None:
        _client = _build()
    return _client


def _build():
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
