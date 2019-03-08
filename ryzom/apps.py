from django.apps import AppConfig


class RyzomConfig(AppConfig):
    name = 'ryzom'

    def ready(self):
        import ryzom.signals
        from ryzom.pubsub import to_publish
        for publication in to_publish:
            publication.publish_all()
