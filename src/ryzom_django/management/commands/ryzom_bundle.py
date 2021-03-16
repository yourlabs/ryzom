import os

from django.core.management.base import BaseCommand, CommandError

from ryzom_django import bundle


class Command(BaseCommand):
    help = 'Write JS & CSS bundles to ryzom_django/static/bundle.*'

    def handle(self, *args, **options):
        static_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                '..',
                '..',
                'static',
            )
        )

        if not os.path.exists(static_path):
            os.makedirs(static_path)

        with open(f'{static_path}/bundle.js', 'w+') as f:
            f.write(bundle.js())

        with open(f'{static_path}/bundle.css', 'w+') as f:
            f.write(bundle.css())

        self.stdout.write(self.style.SUCCESS(f'Successfully wrote {static_path}/bundle.*'))
        self.stdout.write('Do not forget to collectstatic!')
