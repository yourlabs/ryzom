import pytest

from django.conf import settings
from django import views

from ryzom import html
from ryzom_django_channels.views import ReactiveMixin


reactive = pytest.mark.skipif(not settings.CHANNELS_ENABLE, reason='Reactive disabled')
