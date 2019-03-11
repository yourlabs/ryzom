from django.apps import AppConfig
from django.db import OperationalError, ProgrammingError


class RyzomConfig(AppConfig):
    name = 'ryzom'

    def ready(self):
        import ryzom.signals # noqa
        from ryzom.pubsub import to_publish

        try:
            Clients = self.get_model('Clients')
            Clients.objects.all().delete()
            for publication in to_publish:
                publication.publish_all()
        except (OperationalError, ProgrammingError):
            pass
