from django.conf import settings
from django.urls import path, include

urlpatterns = [
    path('', include('ryzom_django_example.forms')),
]

if settings.CHANNELS_ENABLE:
    urlpatterns.append(
        path('reactive/', include('ryzom_django_example.reactive')),
    )
