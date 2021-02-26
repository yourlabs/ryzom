'''
Routes channels websocket incoming message to ryzom.consumers.Consumer
'''
from django.conf.urls import url
from django.core.asgi import get_asgi_application

from . import consumers

websocket_urlpatterns = [
    url(r'^ws/ddp/$', consumers.Consumer.as_asgi()),
    url(r'', get_asgi_application())
]
