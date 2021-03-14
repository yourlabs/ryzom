'''
Defines the HTTP routes to static files and ryzom index.
This will be subject to change in a near future, when implementing SSR
'''
from django.conf import settings
from django.urls import path

from . import views

urlpatterns = [
    path(f'{settings.RYZOM_APP}', views.index, name='index'),
    path('ws/ddp', views.index, name='index'),
    path('<path:url>', views.index, name='index')
]
