from django.conf import settings
from django.db import models

from ryzom_django.pubsub import Publishable, publish


class Task(Publishable, models.Model):
    user = models.ForeignKey(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        on_delete=models.SET_NULL, blank=True, null=True)
    about = models.CharField(max_length=1024)

    class Project:  # app_label - for app-specific model options
        ryzom = True

    def __str__(self):
        return self.about

    @publish('ryzom_django_example.components.Task')
    def all_tasks(cls, user):
        return cls.objects.all()

    @publish('ryzom_django_example.components.Task')
    def user_tasks(cls, user):
        return cls.objects.filter(user=user)


Task.all_tasks(None)
Task.user_tasks(None)
