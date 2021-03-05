import os

from django.conf.urls import url
from django.core.asgi import get_asgi_application


from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from ryzom_django.consumers import Consumer

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    'http': get_asgi_application(),

    'websocket': AuthMiddlewareStack(
        URLRouter([
            url(r"^ws/ddp/$", Consumer.as_asgi()),
        ])
    ),
})
