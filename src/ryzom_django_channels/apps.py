from django.apps import AppConfig
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
        from ryzom_django_channels.pubsub import to_publish

        try:
            Client = self.get_model('Client')
            Client.objects.all().delete()

            for publication in to_publish:
                publication.publish_all()
        except (OperationalError, ProgrammingError):
            pass

        super().ready()
