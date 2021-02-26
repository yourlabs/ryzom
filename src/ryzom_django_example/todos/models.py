from django.conf import settings
from django.db import models

from ryzom.pubsub import Publishable, publish


class Task(Publishable, models.Model):
    user = models.ForeignKey(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        on_delete=models.SET_NULL, blank=True, null=True)
    about = models.CharField(max_length=1024)

    class Project:  # app_label - for app-specific model options
        ryzom = True

    def __str__(self):
        return self.about

    @publish('todos.components.task.Task')
    def all_tasks(cls):
        return cls.objects.all()

    @publish('todos.components.task.Task')
    def first_tasks(cls):
        return cls.objects.all().order_by('about')[0:5]


Task.all_tasks()
Task.first_tasks()
