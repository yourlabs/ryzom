from django.conf import settings
from django.db import models
from django.utils import timezone

from ryzom_django_channels.pubsub import Publishable, publish


class Room(Publishable, models.Model):
    name = models.CharField(max_length=255, unique=True)

    @publish
    def rooms(cls, user):
        return cls.objects.all()


class Message(Publishable, models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True)
    message = models.CharField(max_length=1024)
    created = models.DateTimeField(default=timezone.now)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    class Project:  # app_label - for app-specific model options
        ryzom = True

    def __str__(self):
        return self.message

    @publish
    def messages(cls, user):
        return cls.objects.all()
