import json

from ryzom.components import CList

from ryzom_django_channels.models import (
    Publication,
    Subscription,
    Registration
)


model_templates = dict()


def model_template(name):
    global model_templates
    def decorator(component):
        model_templates[name] = component
        return component
    return decorator


class ReactiveBase:
    view = None

    def to_html(self, *content, **context):
        self.reactive_setup(**context)
        return super(ReactiveBase, self).to_html(*content, **context)

    def reactive_setup(self, **context):
        self.view = self.get_view(**context)

        if self.view is None:
            parent = self.parent or self
            while parent and parent.parent:
                if hasattr(parent, 'view'):
                    break
                parent = parent.parent
            try:
                self.view = parent.view
            except AttributeError:
                raise AttributeError('The current view cannot be found')

        if not hasattr(self.view, 'client'):
            raise AttributeError(
                'The current view has no attribute "client".'
                ' Maybe you forgot to call view.get_token()'
                ' in your main component?')

    def get_view(self, **context):
        if 'view' in context:
            return context['view']


class SubscribeComponentMixin(ReactiveBase):
    # Declarative filter: a list of facets (see ryzom_django_channels.facets).
    # The default get_queryset applies them forward; the signal handler reuses
    # the same facets in reverse to route a change to only the affected
    # subscriptions. Subscribers may still override get_queryset instead.
    facets = []

    @property
    def model_template(self):
        raise AttributeError(
            f'{self} is missing attribute "model_template"'
        )

    def reactive_setup(self, **context):
        if not hasattr(self, 'subscribe_options'):
            self.subscribe_options = {}

        super().reactive_setup(**context)

        if hasattr(self, 'publication'):
            self.create_subscription()


    def create_subscription(self):
        '''Render the first page read-only and emit a subscribe descriptor.

        No Subscription/Client row is written here — a GET must stay safe (see
        ``ReactiveMixin.get_token``). A *transient* (unsaved) Subscription
        computes the initial window for the first paint, so a JS-less crawler
        still gets fully-rendered rows. The ``data-ryzom-subscribe`` descriptor
        lets the client re-create the Subscription over its transport (the
        websocket ``recv_subscribe`` or the first poll POST), which is the only
        place it is persisted. See PROBLEM.md.
        '''
        subscriber_id = getattr(self, 'container', self).id
        publication = Publication.objects.get(name=self.publication)
        self.subscription = Subscription(
            client=self.view.client,
            publication=publication,
            subscriber_id=subscriber_id,
            subscriber_module=self.__module__,
            subscriber_class=self.__class__.__name__,
            options=self.subscribe_options,
        )

        self.get_content()

        container = getattr(self, 'container', self)
        container.attrs['data-ryzom-subscribe'] = '1'
        container.attrs['data-publication'] = publication.name
        container.attrs['data-subscriber-id'] = subscriber_id
        container.attrs['data-subscriber-module'] = self.__module__
        container.attrs['data-subscriber-class'] = self.__class__.__name__
        container.attrs['data-subscribe-options'] = json.dumps(
            self.subscribe_options or {})

    def get_content(self):
        template = model_templates[self.model_template]

        content = []
        # persist=False: the transient subscription computes the window without
        # writing; the row is created later when the client subscribes.
        self.queryset = self.subscription.get_queryset(persist=False)
        for obj in self.queryset:
            content.append(template(obj))

        container = getattr(self, 'container', self)
        container.content = content

    @classmethod
    def get_queryset(cls, usr, qs, opts):
        opts = opts or {}
        for facet in cls.facets:
            qs = facet.forward(qs, opts.get(facet.key), usr)
        return qs


class ReactiveComponentMixin(ReactiveBase):
    register = None

    def reactive_setup(self, **context):
        super().reactive_setup(**context)

        if hasattr(self, 'register'):
            self.create_registration()

    def create_registration(self):
        '''Emit a register descriptor; do not write on the page GET.

        Like ``create_subscription``, this stays read-only so the GET is safe
        and crawlers create nothing. The Registration is (idempotently) created
        when the client replays the ``data-ryzom-register`` descriptor over its
        transport (see ``polling.establish``).
        '''
        if isinstance(self, CList):
            raise Exception('Cannot register from CList')

        self.attrs['data-ryzom-register'] = '1'
        self.attrs['data-register-name'] = self.get_register()
        self.attrs['data-subscriber-id'] = self.id
        self.attrs['data-subscriber-parent'] = self.parent.id
        self.attrs['data-subscriber-class'] = self.__class__.__name__
        self.attrs['data-subscriber-module'] = self.__module__

    def get_register(self):
        if self.register is None:
            raise AttributeError(f'{self}.register is not defined')

        return self.register
