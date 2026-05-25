# ryzom_django_channels

Real-time reactive features using Django Channels and WebSockets.

## Overview

ryzom_django_channels enables real-time reactive web applications by implementing a pub/sub system with server-side component registration and automatic DOM updates. Components subscribe to published querysets, and the server pushes HTML updates over WebSockets when data changes.

## Installation

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'channels',
    'ryzom_django_channels',
]
```

Configure Django Channels with Redis or another channel layer.

## Features

### Publishable Models

Mark queryset methods for subscription:

```python
from django.db import models
from ryzom_django_channels.pubsub import Publishable, publish

class Article(Publishable, models.Model):
    title = models.CharField(max_length=255)
    published = models.BooleanField(default=False)

    @publish
    def latest(cls, user):
        return cls.objects.filter(published=True).order_by('-created')
```

### Subscribing Components

Bind components to publications:

```python
from ryzom_django_channels.components import SubscribeComponentMixin, model_template
from ryzom.html import Li, Ul

@model_template('article-row')
class ArticleRow(Li):
    def __init__(self, article):
        super().__init__(article.title, id=f'article-{article.pk}')

class ArticleList(SubscribeComponentMixin, Ul):
    publication = 'latest'
    model_template = 'article-row'
```

### Server-Driven Refresh

Refresh components from anywhere on the server:

```python
from ryzom_django_channels.views import register

def on_data_changed():
    register('my-component').refresh(new_data='value')
```

### Reactive Views

Mix in `ReactiveMixin` to enable WebSocket connections:

```python
from django.views import generic
from ryzom_django_channels.views import ReactiveMixin

class DashboardView(ReactiveMixin, generic.TemplateView):
    template_name = 'dashboard'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['token_script'] = self.get_token()
        return ctx
```

### Batching with Subscription Locks

Long server-side jobs that produce a stream of `save()`/`delete()` calls
will fire one Celery task per signal by default — fine for ten edits,
problematic for a thousand. A subscription lock lets you tell the system
"hold updates for *these* subscribers, replay them as one batch when I'm
done", while every other subscriber on the same model continues to get
live updates.

#### How it works

While a `Subscription` is locked, `post_save`/`post_delete` signals for
its model push events to a Redis queue keyed by subscription id rather
than dispatching a per-signal Celery task for that subscription. On
release, a single `ddp_flush_task` drains the queue, coalesces events
per instance, computes the queryset delta once, and emits the final DDP
messages.

Coalescing rules per instance within a lock window:

| Sequence                     | Emitted    |
|------------------------------|------------|
| `save()`, `save()`, …        | `change`   |
| `save()` then `delete()`     | `remove`   |
| `create()` then `delete()`   | *(nothing)*|
| `delete()` alone             | `remove`   |

Locks are reentrant (counter-based), survive across processes (stored
in Redis), and time out at one hour as a safety net if a worker dies
mid-job.

#### Locking a single subscription

```python
sub = Subscription.objects.get(pk=sub_id)
with sub.lock():
    for thing in big_list:
        Model.objects.create(...)
# release: one ddp_flush_task processes the coalesced events
```

#### Locking a set of subscriptions matching a scope

The `Subscription.options` JSONField is the canonical way to scope a
subscription (your `publish_function` and `subscriber.get_queryset` read
it to narrow the queryset). It's also what you query against to find
the subs to lock — same key, no duplicate source of truth.

```python
from ryzom_django_channels.locks import lock_subscriptions

# Subscribers narrow by group_id via options:
class GroupMembers(SubscribeComponentMixin, Ul):
    publication = 'group_members'
    model_template = 'member-row'

    @classmethod
    def get_queryset(cls, user, qs, opts):
        return qs.filter(group_id=opts['group_id'])

# Long-running import job:
group_subs = Subscription.objects.filter(
    publication__name='group_members',
    options__group_id=group.id,
)

with lock_subscriptions(group_subs):
    for row in csv_rows:
        User.objects.create(group=group, ...)
# release: one flush task per locked sub, each with coalesced events;
# subscribers to OTHER groups got live updates throughout.
```

Any predicate you'd put in a `get_queryset` filter works as a lookup
filter too:

```python
# scope by client/user
Subscription.objects.filter(
    publication__name='my_threads',
    client__user=request.user,
)

# scope by nested options key
Subscription.objects.filter(options__filters__contains={'tag': 'imported'})
```

#### Imperative API

If a `with` block doesn't fit, pair `acquire_lock()` / `release_lock()`
manually:

```python
sub.acquire_lock()
try:
    do_work()
finally:
    sub.release_lock()  # returns True when the counter hits 0 and a flush is dispatched
```

#### Trade-offs to be aware of

- **Sub set is materialized at `with` entry.** Subscriptions created
  *during* the job are not in the locked set and will receive live
  updates as usual. Subscriptions deleted during the job have their
  flush task no-op cleanly. If you need "subs that appear mid-job
  should also batch", lock by predicate rather than by id — that's a
  larger change, ask before relying on it.
- **Other subscribers still incur a task per signal.** If only some
  subs of a model are locked, the per-signal Celery task is still
  dispatched to handle the unlocked ones (with the locked sub ids
  passed as `excluded_subs`). The savings come from skipping the
  locked sub's per-signal work and replaying it as one flush, not from
  suppressing the task entirely.
- **Lock state is global (Redis).** A lock acquired in one process
  affects signals fired in any other process/worker. Make sure every
  `acquire_lock()` is matched by a `release_lock()` (use the context
  manager whenever possible).

## See Also

- [Main README](../../README.md) for complete documentation
- [Reactive documentation](../../docs/source/ryzom.reactive.rst) for detailed patterns
- [ryzom](../ryzom/README.md) for core components
