from django.conf.urls import url
from .pages import Layout

ddp_urlpatterns = [
    url(r'todos', Layout),
    url(r'', Layout),
]
