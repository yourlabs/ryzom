'''
Routes channels websocket incoming message to ryzom.consumers.Consumer
'''
from django.core.asgi import get_asgi_application
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/ddp/$', consumers.Consumer.as_asgi()),
    re_path(r'', get_asgi_application())
]
