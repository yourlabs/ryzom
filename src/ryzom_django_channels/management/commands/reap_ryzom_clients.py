'''
Delete stale ryzom Clients (and their cascaded Subscriptions/Registrations).

The consumer reaps opportunistically on every WebSocket disconnect, but on a
quiet system few disconnects fire, so detached clients can accumulate. Schedule
this command (cron / celery-beat) to bound the Client table regardless.
'''
from django.core.management.base import BaseCommand

from ryzom_django_channels.models import Client


class Command(BaseCommand):
    help = (
        'Delete stale ryzom Clients: ws clients detached longer than '
        'RYZOM_CLIENT_GRACE_SECONDS (default 900s) and never-attached zombies.'
    )

    def handle(self, *args, **options):
        before = Client.objects.count()
        Client.reap_stale()
        reaped = before - Client.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f'Reaped {reaped} stale client(s).'))
