from django.conf import settings
from django.conf.urls import url

from .views import Layout

urlpatterns = [
    url(settings.RYZOM_APP, Layout),
    url(r'', Layout),
]
