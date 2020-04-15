from django.apps import AppConfig
from django.db import OperationalError, ProgrammingError


class RyzomConfig(AppConfig):
    '''
    Ryzom application configuration
    '''
    name = 'ryzom'

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
        try:
            import ryzom.signals  # noqa
        except (ImportError,):
            pass

        from ryzom.pubsub import to_publish

        try:
            Clients = self.get_model('Clients')
            Clients.objects.all().delete()
            for publication in to_publish:
                publication.publish_all()
        except (OperationalError, ProgrammingError):
            pass
