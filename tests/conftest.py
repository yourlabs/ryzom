import pytest


@pytest.fixture(autouse=True, scope='session')
def _initial_widget_templates():
    """Capture widget_templates state before any URL conf loads (e.g. simple.py)."""
    from ryzom_django.forms import widget_templates
    return dict(widget_templates)


@pytest.fixture(autouse=True)
def isolate_widget_templates(_initial_widget_templates):
    """Restore widget_templates to the pre-URL-conf state before every test."""
    from ryzom_django.forms import widget_templates
    widget_templates.clear()
    widget_templates.update(_initial_widget_templates)
    yield
    widget_templates.clear()
    widget_templates.update(_initial_widget_templates)
