from ryzom_django_channels.models import (
    Publication,
    Subscription,
    Registration
)

class ReactiveBase:
    view = None

    def to_html(self, **kwargs):
        self.reactive_setup()
        return super(ReactiveBase, self).to_html(**kwargs)

    def reactive_setup(self):
        self.set_view()

    def set_view(self):
        if not hasattr(self, 'view') or self.view is None:
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

        return self.view


class SubscribeComponentMixin(ReactiveBase):
    def reactive_setup(self):
        subscribe_options = {}
        if hasattr(self, 'subscribe_options'):
            subscribe_options = self.subscribe_options

        super().reactive_setup()

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
        template = publication.get_template()

        content = []
        for obj in subscription.get_queryset():
            content.append(template(obj))

        self.content = content

    @classmethod
    def get_queryset(self, qs, opts):
        return qs


class ReactiveComponentMixin(ReactiveBase):
    register = None

    def reactive_setup(self):
        super().reactive_setup()

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
