'''
Per-subscription batching locks.

When a Subscription is locked, post_save/post_delete signals for its
publication's model push events to a Redis queue keyed by subscription
id, instead of dispatching the regular Celery task path that would
process this subscription. Other (unlocked) subscriptions on the same
model continue to receive live updates.

On release, a single ddp_flush_task drains the subscription's queue,
coalesces events per instance, computes the qs delta once, and emits
the final DDP messages.

Coalescing rules per instance within a lock window:
  - repeated save()         -> one `change` (final state from DB)
  - save() then delete()    -> one `remove`
  - create() then delete()  -> nothing
  - delete() alone          -> one `remove`
'''
import contextlib
import json

from ryzom_django_channels import celery_app
from ryzom_django_channels.redis_conn import get_redis as _get_redis


_LOCK_KEY = 'ryzom:sub:{sid}:lock'
_QUEUE_KEY = 'ryzom:sub:{sid}:queue'
_BY_MODEL_KEY = 'ryzom:locked_subs_by_model:{mod}.{cls}'
_QUEUE_TTL = 3600  # 1h safety net if a worker dies holding a lock


def _decode(members):
    return {m.decode() if isinstance(m, bytes) else m for m in members}


def locked_subs_for_model(mod, cls):
    '''Return the set of locked subscription ids (as strings) for this model.'''
    return _decode(_get_redis().smembers(_BY_MODEL_KEY.format(mod=mod, cls=cls)))


def lock(sub_id, mod, cls):
    '''Increment the lock counter for a subscription.'''
    sid = str(sub_id)
    r = _get_redis()
    pipe = r.pipeline()
    pipe.incr(_LOCK_KEY.format(sid=sid))
    pipe.sadd(_BY_MODEL_KEY.format(mod=mod, cls=cls), sid)
    pipe.execute()


def release(sub_id, mod, cls):
    '''
    Decrement the lock counter; when it reaches 0, clear the index entry
    and dispatch ddp_flush_task to drain the accumulated events.
    Returns True if a flush was triggered.
    '''
    sid = str(sub_id)
    r = _get_redis()
    count = r.decr(_LOCK_KEY.format(sid=sid))
    if count <= 0:
        pipe = r.pipeline()
        pipe.delete(_LOCK_KEY.format(sid=sid))
        pipe.srem(_BY_MODEL_KEY.format(mod=mod, cls=cls), sid)
        pipe.execute()
        ddp_flush_task.delay(sid)
        return True
    return False


@contextlib.contextmanager
def lock_subscriptions(subs):
    '''
    Context manager that locks every subscription in the given queryset
    or iterable for the duration of the with-block. Each lock is released
    independently on exit, triggering one flush task per subscription.

    Materializes the queryset up-front so the same set is locked and
    released even if matching rows change during the block.
    '''
    subs = list(subs)
    for s in subs:
        s.acquire_lock()
    try:
        yield subs
    finally:
        for s in subs:
            s.release_lock()


def enqueue(sub_id, event):
    '''Append an event dict to the subscription's pending queue.'''
    r = _get_redis()
    key = _QUEUE_KEY.format(sid=str(sub_id))
    pipe = r.pipeline()
    pipe.rpush(key, json.dumps(event))
    pipe.expire(key, _QUEUE_TTL)
    pipe.execute()


def drain(sub_id):
    '''Atomically pop all queued events for a subscription.'''
    r = _get_redis()
    key = _QUEUE_KEY.format(sid=str(sub_id))
    pipe = r.pipeline()
    pipe.lrange(key, 0, -1)
    pipe.delete(key)
    items, _ = pipe.execute()
    return [json.loads(x) for x in items]


@celery_app.task()
def ddp_flush_task(sub_id):
    from ryzom_django_channels.components import model_templates
    from ryzom_django_channels.ddp import (
        send_change, send_insert, send_remove,
    )
    from ryzom_django_channels.models import Subscription

    events = drain(sub_id)
    if not events:
        return

    # Per-instance coalescing: track whether we ever saw a create, and
    # the most recent op. Drop create+delete pairs entirely.
    state = {}
    for ev in events:
        iid = ev['instance_id']
        op = ev['op']
        s = state.setdefault(iid, {'created': False, 'last_op': None})
        if op == 'save' and ev.get('created') and s['last_op'] is None:
            s['created'] = True
        s['last_op'] = op

    touched = {
        iid: s['last_op']
        for iid, s in state.items()
        if not (s['created'] and s['last_op'] == 'delete')
    }
    if not touched:
        return

    from django.db import transaction

    # Same per-subscription row lock as the live signal path (signals.py):
    # serializes against concurrent DDP tasks so the qs delta is computed
    # from a consistent snapshot.
    with transaction.atomic():
        sub = (
            Subscription.objects
            # of=('self',): see signals.for_each_subscription — nullable FK
            # joins can't be FOR UPDATE locked, and the subscription row is
            # the only one we need to serialize on.
            .select_for_update(of=('self',))
            .select_related('publication', 'client', 'client__user')
            .filter(pk=sub_id)
            .first()
        )
        if sub is None or sub.client is None:
            return

        model = sub.publication.model
        template = model_templates[sub.subscriber.model_template]
        to_python = model.id.field.to_python

        old_qs_strings = set(sub.qs)
        qs = sub.get_queryset()
        if not qs.query.can_filter():
            qs.query.clear_limits()
        new_qs_strings = set(sub.qs)

        for iid, last_op in touched.items():
            in_old = iid in old_qs_strings
            in_new = iid in new_qs_strings

            if in_old and not in_new:
                obj = model.objects.filter(pk=to_python(iid)).first()
                if obj is None:
                    obj = model(id=to_python(iid))
                send_remove(sub, template, obj)
            elif not in_old and in_new:
                send_insert(sub, template, qs.get(pk=to_python(iid)))
            elif in_old and in_new and last_op == 'save':
                send_change(sub, template, qs.get(pk=to_python(iid)))
