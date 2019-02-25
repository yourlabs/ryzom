from django.urls import path

from . import views

urlpatterns = [
        path('<path:url>', views.index, name='index'),
]
