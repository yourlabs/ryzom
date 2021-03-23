from django.apps import AppConfig, apps
from django.db import OperationalError, ProgrammingError


class BaseConfig(AppConfig):
    '''
    Ryzom application configuration
    '''
    name = 'ryzom_django_channels'

    def ready(self):
        '''
        AppConfig.ready overloading.

        Here we import the ryzom.signals module to connect the signals handlers
        to receivers, then we clean the Clients table (zombies clients stay
        after a server reboot).

        Finally, we create the publications that were registered
        in the to_publish list of ryzom.pusub module.
        '''
        import ryzom_django_channels.signals
        from ryzom_django_channels.pubsub import Publishable

        try:
            Client = self.get_model('Client')
            Client.objects.all().delete()

            for model in apps.get_models():
                if issubclass(model, Publishable):
                    model.publish()

        except (OperationalError, ProgrammingError):
            pass

        super().ready()
