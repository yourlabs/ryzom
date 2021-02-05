from django.conf import settings
from django.urls import re_path

from .views import Layout

urlpatterns = [
    re_path(settings.RYZOM_APP, Layout),
    re_path(r'', Layout),
]
