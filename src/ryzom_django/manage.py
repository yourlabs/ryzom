import os
import sys
import warnings


def main(settings_module=None):
    os.environ.setdefault(
        'DJANGO_SETTINGS_MODULE',
        settings_module or 'ryzom_example.settings'
    )

    if 'DEBUG' not in os.environ:
        warnings.warn('DEFAULTING DEBUG=1')
        os.environ.setdefault('DEBUG', '1')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            'Couldn\'t import Django. Are you sure it\'s installed and '
            'available on your PYTHONPATH environment variable? Did you '
            'forget to activate a virtual environment?'
        ) from exc
    execute_from_command_line(sys.argv)
