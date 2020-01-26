from django.conf.urls import url
from todos.views import Layout

urlpatterns = [
    url(r'todos', Layout),
    url(r'', Layout),
]
