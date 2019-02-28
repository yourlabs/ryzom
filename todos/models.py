from django.db import models
from django.contrib.auth.models import User


class Tasks(models.Model):
    user = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)
    about = models.CharField(max_length=1024)
