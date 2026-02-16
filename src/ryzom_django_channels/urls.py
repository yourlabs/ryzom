from django.urls import path

from ryzom_django_channels.polling import (
    PollReceiveView,
    PollSendView,
    TransportSwitchView,
)

urlpatterns = [
    path('ddp/send/', PollSendView.as_view(), name='ryzom-poll-send'),
    path('ddp/poll/', PollReceiveView.as_view(), name='ryzom-poll-receive'),
    path('ddp/switch/', TransportSwitchView.as_view(), name='ryzom-poll-switch'),
]
