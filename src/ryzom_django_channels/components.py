from ryzom.components import CList

from ryzom_django_channels.models import (
    Publication,
    Subscription,
    Registration
)


model_templates = dict()


def model_template(name_or_serializer):
    global model_templates

    # Accept a DRF serializer class: derive the template name from it
    if isinstance(name_or_serializer, type) and hasattr(name_or_serializer, 'Meta'):
        serializer_class = name_or_serializer
        name = f'drf-{serializer_class.Meta.model._meta.label_lower}'

        def decorator(component):
            model_templates[name] = component
            # Also register in the ryzom_drf item cache if available
            try:
                from ryzom_drf.components import _item_components
                _item_components[serializer_class] = component
            except ImportError:
                pass
            return component
        return decorator

    # Original behavior: accept a string name
    name = name_or_serializer

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
            # Walk up to the first ancestor carrying an actual view. The
            # previous version stopped at the first ancestor *having* a
            # `view` attribute — but ReactiveBase defines `view = None` as a
            # class attribute, so an intermediate reactive ancestor with no
            # view yet would mask a higher ancestor that has one.
            parent = self.parent
            while parent is not None:
                view = getattr(parent, 'view', None)
                if view is not None:
                    self.view = view
                    break
                parent = getattr(parent, 'parent', None)
            if self.view is None:
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
        subscriber_id = getattr(self, 'container', self).id
        publication = Publication.objects.get(name=self.publication)
        self.subscription = Subscription.objects.create(
            client=self.view.client,
            publication=publication,
            subscriber_id=subscriber_id,
            subscriber_module=self.__module__,
            subscriber_class=self.__class__.__name__,
            options=self.subscribe_options,
        )

        self.get_content()

    def get_content(self):
        template = model_templates[self.model_template]

        content = []
        self.queryset = self.subscription.get_queryset()
        for obj in self.queryset:
            content.append(template(obj))

        container = getattr(self, 'container', self)
        container.content = content

    @classmethod
    def get_queryset(self, usr, qs, opts):
        return qs


class ReactiveComponentMixin(ReactiveBase):
    register = None

    def reactive_setup(self, **context):
        super().reactive_setup(**context)

        if hasattr(self, 'register'):
            self.create_registration()

    def create_registration(self):
        if isinstance(self, CList):
            raise Exception('Cannot register from CList')

        # Atomic upsert on the (name, client) unique key — the previous
        # filter-then-create pattern could raise IntegrityError under
        # concurrent renders of the same client.
        Registration.objects.update_or_create(
            name=self.get_register(),
            client=self.view.client,
            defaults=dict(
                subscriber_id=self.id,
                subscriber_parent=self.parent.id,
                subscriber_class=self.__class__.__name__,
                subscriber_module=self.__module__,
            ),
        )

    def get_register(self):
        if self.register is None:
            raise AttributeError(f'{self}.register is not defined')

        return self.register
