'''
Defines the HTTP routes to static files and ryzom index.
This will be subject to change in a near future, when implementing SSR
'''
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static


from . import views

urlpatterns = static('ryzom/static/', document_root='ryzom/static/') + \
        static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + [
        path('', views.index, name='index'),
        path('<path:url>', views.index, name='index')
]
