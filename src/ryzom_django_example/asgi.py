import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from django.core.asgi import get_asgi_application

from ryzom_django_channels.consumers import Consumer

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    'http': get_asgi_application(),

    'websocket': AuthMiddlewareStack(
        URLRouter([
            re_path(r"^ws/ddp/$", Consumer.as_asgi()),
        ])
    ),
})
