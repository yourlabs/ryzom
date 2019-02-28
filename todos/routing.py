from django.conf.urls import url
from .pages import Layout

urlpatterns = [
    url(r'todos', Layout),
    url(r'', Layout),
]
