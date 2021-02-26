from django.apps import AppConfig
from django.db import OperationalError, ProgrammingError
from django.utils.module_loading import autodiscover_modules


class BaseConfig(AppConfig):
    name = 'ryzom_django'

    def ready(self):
        autodiscover_modules('components')
        super().ready()


class ReactiveConfig(BaseConfig):
    '''
    Ryzom application configuration
    '''

    def ready(self):
        '''
        AppConfig.ready overloading.
        Here we import the ryzom.signals module to connect
        the signals handlers to receivers,
        then we clean the Clients table (zombies clients stay after
        a server reboot)
        Finally, we create the publications that were registered
        in the to_publish list of ryzom.pusub module.
        '''
        import ryzom_django.signals

        from ryzom_django.pubsub import to_publish

        try:
            Clients = self.get_model('Clients')
            Clients.objects.all().delete()
            Subscriber = self.get_model('Subscriber')
            Subscriber.objects.all().delete()

            for publication in to_publish:
                publication.publish_all()
        except (OperationalError, ProgrammingError):
            pass

        super().ready()
