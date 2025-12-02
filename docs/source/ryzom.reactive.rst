Reactive views with ryzom_django_channels
=========================================

Ryzom ships with ``ryzom_django_channels`` to push HTML fragments over
websockets and keep clients in sync with server-side state. The pattern is:

- a Django view uses ``ReactiveMixin`` to hand out a websocket token;
- models inherit ``Publishable`` and expose one or more ``@publish`` query
  methods;
- components subscribe to those publications with
  ``SubscribeComponentMixin`` and render rows defined by
  ``@model_template``;
- any component can declare a ``register`` name via
  ``ReactiveComponentMixin`` and be refreshed from arbitrary server code with
  ``register('<name>').refresh(...)``.


Wiring a reactive page
----------------------

In a Django view, mix in ``ReactiveMixin`` and render the JS token (required so
the browser connects to the websocket layer):: 

    from django.views import generic
    from ryzom_django_channels.views import ReactiveMixin
    from ryzom_mdc.html import *

    class DashboardView(ReactiveMixin, generic.TemplateView):
        template_name = 'dashboard'

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            ctx['token_script'] = self.get_token()  # pass to your root component
            return ctx


Concrete view + template example
--------------------------------

Here is a minimal Django view and template that wire everything together and
show where the ``get_token`` output should live in the page::

    # views.py
    from django.utils.safestring import mark_safe
    from django.views import generic
    from ryzom_django_channels.views import ReactiveMixin
    from .components import ArticleList  # your SubscribeComponentMixin subclass

    class ArticleDashboard(ReactiveMixin, generic.TemplateView):
        template_name = 'articles'

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            ctx['articles'] = ArticleList()
            ctx['token_script'] = mark_safe(self.get_token())
            return ctx

The matching Django template renders your reactive component and the websocket
token inside a Ryzom template so the JS runs after the DOM is built::

    # templates.py
    from ryzom.html import Html, Script, template

    @template('articles')  # template_name matches the view
    class Articles(Html):
        scripts = ['/static/ryzom.js']

        def to_html(self, *content, view, articles, token_script, **context):
            head, body = content
            body.addchildren([
                articles,
                Script(token_script),  # set window.token and call ws_connect()
            ])
            return super().to_html(head, body)

Place ``Script(token_script)`` after your root component so ``window.token`` is
set and ``ws_connect`` runs once the page structure exists.

Publishing data from models
---------------------------

Attach ``Publishable`` to any model and mark queryset factories with
``@publish``. Each published method becomes a ``Publication`` that subscribers
can target::

    from django.db import models
    from ryzom_django_channels.pubsub import Publishable, publish

    class Article(Publishable, models.Model):
        title = models.CharField(max_length=255)
        body = models.TextField()
        created = models.DateTimeField(auto_now_add=True)
        published = models.BooleanField(default=False)

        @publish
        def latest(cls, user):
            # user is available to enforce per-user access rules
            return cls.objects.filter(published=True).order_by('-created')

``Publishable.publish()`` is called at startup by the app config and records
the publication so clients can subscribe. The published method name (``latest``
above) is the publication identifier clients will use.


Subscribing in components
-------------------------

Use ``SubscribeComponentMixin`` to bind a component to a publication and
``@model_template`` to describe how each model instance is rendered::

    from ryzom_django_channels.components import (
        SubscribeComponentMixin,
        model_template,
    )
    from ryzom.html import *

    @model_template('article-row')
    class ArticleRow(Li):
        def __init__(self, article):
            super().__init__(article.title, id=f'article-{article.pk}')

    class ArticleList(SubscribeComponentMixin, Ul):
        publication = 'latest'
        model_template = 'article-row'

        def __init__(self, search=None, page_size=20):
            # Passed to the subscription and available in get_queryset
            self.subscribe_options = dict(q=search or '', limit=page_size)
            super().__init__()

        @classmethod
        def get_queryset(cls, user, qs, opts):
            query = qs.filter(published=True)
            if term := opts.get('q'):
                query = query.filter(title__icontains=term)
            limit = max(1, min(int(opts.get('limit', 20)), 200))
            return query.order_by('-created')[:limit]

When the component renders, a ``Subscription`` row is created that records the
client, publication, component id, and the options you provided. Whenever the
underlying queryset changes, inserts/updates/removals are pushed to the client.

You can implement pagination and filters by carrying extra keys inside
``subscribe_options`` (for example ``p``, ``psize``, ``status``) and consuming
them in ``get_queryset`` just like above.


Server-driven refresh with registers
------------------------------------

Any component can be refreshed on demand without a publication by declaring a
``register`` name via ``ReactiveComponentMixin``::

    from ryzom_django_channels.components import ReactiveComponentMixin
    from ryzom.html import Div

    class QueueSummary(ReactiveComponentMixin, Div):
        register = 'queue:summary'

        def __init__(self, open_count, waiting_count):
            super().__init__(
                f'{open_count} open / {waiting_count} waiting',
                cls='queue-summary',
            )

From anywhere on the server (views, signals, Celery tasks) you can push a new
render of that component to connected clients::

    from ryzom_django_channels.views import register

    def on_ticket_created(open_count, waiting_count):
        register('queue:summary').refresh(
            open_count=open_count,
            waiting_count=waiting_count,
        )

The registration table is maintained automatically per client, keyed by the
``register`` value and the component id. If a client is not yet connected, the
refresh is deferred for a short time and sent when the websocket attaches.


Example project
---------------

The bundled example apps illustrate different reactive patterns:

- ``src/ryzom_django_channels_example`` shows a simple chat:

- models define ``Room`` and ``Message`` publications;
- ``ChatRoom`` subscribes with filtering and ordering options;
- ``ReactiveTitle`` uses ``register`` to update the page title when messages
  change;
- ``ReactiveMixin.get_token()`` is rendered in the page so the browser connects
  to Channels.

- Browse ``src/ryzom_django_channels_example`` for a minimal, end-to-end
  reactive setup you can drop into a Django project.


API reference
-------------

.. automodule:: ryzom.reactive
    :members:
    :undoc-members:
    :show-inheritance:
