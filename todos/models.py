from django.db import models
from django.contrib.auth.models import User
from ryzom.pubsub import Publishable


class Task(models.Model, Publishable):
    user = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)
    about = models.CharField(max_length=1024)


Task.publish(
        name='task',
        template='todos.components.tasks.Task',
        query=[
            {'order_by': 'about'},
            {'offset': ('$count', -5)},
            {'limit': 5},
        ]
)
