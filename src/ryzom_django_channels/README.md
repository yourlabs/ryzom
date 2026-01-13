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

## See Also

- [Main README](../../README.md) for complete documentation
- [Reactive documentation](../../docs/source/ryzom.reactive.rst) for detailed patterns
- [ryzom](../ryzom/README.md) for core components
