'''
Routes channels websocket incoming message to ryzom.consumers.Consumer
'''
from django.conf.urls import url

from . import consumers

websocket_urlpatterns = [
    url(r'^ws/ddp/$', consumers.Consumer.as_asgi()),
]
'''
The route to the consumer
'''
