from django.conf import settings
from django.urls import include, path

from ryzom_django_example.crud import UserRouter

urlpatterns = (
    # home/ login/ logout/ at root so reverse('login') works globally
    UserRouter.get_auth_urls()
    + [
        path('', include('ryzom_django_example.views')),
        path('tutorial/', include('ryzom_django_example.tutorial')),
        path('crud/users/', include('ryzom_django_example.crud')),
    ]
)

if settings.DEBUG:
    urlpatterns += [path('bundles/', include('ryzom_django.bundle'))]

if settings.CHANNELS_ENABLE:
    urlpatterns.append(
        path('reactive/', include('ryzom_django_channels_example.views')),
    )
