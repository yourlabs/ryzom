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
        publication = Publication.objects.get(name=self.publication)
        subscription = Subscription.objects.create(
            client=self.view.client,
            publication=publication,
            subscriber_id=self.id,
            subscriber_module=self.__module__,
            subscriber_class=self.__class__.__name__,
            options=self.subscribe_options,
        )

        self.get_content(publication, subscription)

    def get_content(self, publication, subscription):
        template = model_templates[self.model_template]

        content = []
        for obj in subscription.get_queryset():
            content.append(template(obj))

        self.content = content

    @classmethod
    def get_queryset(self, qs, opts):
        return qs


class ReactiveComponentMixin(ReactiveBase):
    register = None

    def reactive_setup(self, **context):
        super().reactive_setup(**context)

        if hasattr(self, 'register'):
            self.create_registration()

    def create_registration(self):
        existent = Registration.objects.filter(
            name=self.get_register(),
            client=self.view.client
        ).first()

        if existent:
            existent.subscriber_id = self.id
            existent.subscriber_parent = self.parent.id
            existent.save()

        else:
            Registration.objects.create(
                name=self.get_register(),
                client=self.view.client,
                subscriber_id=self.id,
                subscriber_parent=self.parent.id,
            )

    def get_register(self):
        if self.register is None:
            raise AttributeError(f'{self}.register is not defined')

        return self.register
