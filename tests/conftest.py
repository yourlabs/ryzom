import sys
import pytest


@pytest.fixture(autouse=True, scope='session')
def _initial_widget_templates():
    """Capture widget_templates state before any URL conf loads (e.g. tutorial.py)."""
    from ryzom_django.forms import widget_templates
    return dict(widget_templates)


@pytest.fixture(autouse=True)
def isolate_widget_templates(_initial_widget_templates):
    """Restore widget_templates to the pre-URL-conf state before every test."""
    from django.urls import clear_url_caches
    from ryzom_django.forms import widget_templates

    # Drop URL conf modules so the next URL resolution re-imports them fresh.
    # This guarantees simple.py's @widget_template decorators run again during
    # test_view_get even when a prior test (e.g. a channels Consumer) already
    # loaded the URL conf and triggered the simple.py import.
    for mod in ('ryzom_django_example.tutorial', 'ryzom_django_example.urls'):
        sys.modules.pop(mod, None)
    clear_url_caches()

    widget_templates.clear()
    widget_templates.update(_initial_widget_templates)
    yield
    widget_templates.clear()
    widget_templates.update(_initial_widget_templates)
