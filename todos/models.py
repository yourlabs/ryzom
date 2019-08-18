from django.conf import settings
from django.db import models
from ryzom.pubsub import Publishable


class Task(models.Model, Publishable):
    user = models.ForeignKey(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        on_delete=models.SET_NULL, blank=True, null=True)
    about = models.CharField(max_length=1024)


Task.publish(
        name='task',
        template='todos.components.task.Task',
        query=[
            {'order_by': 'about'},
            {'offset': ('$count', -5)},
            {'limit': 5},
        ]
)
