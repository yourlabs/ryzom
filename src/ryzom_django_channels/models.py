'''
This file defines the models needed for ryzom pub/sub system.
They're not intended to be used by end-user.
'''
import importlib
import secrets
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.db.models import JSONField
from django.utils import timezone


class Client(models.Model):
    '''
    Clients are the representation of connected Clients
    over websockets. It stores the channel name of a single
    client to communicate over the channel layer
    The user field is not used for now but in a near future
    it will be used to store the user using this channel
    once it's connected
    '''
    token = models.CharField(default=secrets.token_urlsafe,
                             max_length=255, unique=True)
    channel = models.CharField(max_length=255)
    user = models.ForeignKey(
                settings.AUTH_USER_MODEL,
                models.SET_NULL,
                blank=True,
                null=True
           )
    created = models.DateTimeField(default=timezone.now)


class Registration(models.Model):
    name = models.CharField(max_length=255)
    client = models.ForeignKey(Client, models.CASCADE, blank=True, null=True)
    subscriber_id = models.CharField(max_length=255)
    subscriber_parent = models.CharField(max_length=255)

    class Meta:
        unique_together = [('name', 'client')]


class Publication(models.Model):
    '''
    Publications model is used to store the apps publications
    Each publication should have a unique name and define
    the component used as template for the publicated model.
    One can publish a model multiple time with varying templates
    or query.
    The query is a JSON field containing informations on what and
    how to publish about the model concerned, such as
    order_by, limit, offset, filters and more soon
    '''
    name = models.CharField(max_length=255, unique=True)
    model_module = models.CharField(max_length=255)
    model_class = models.CharField(max_length=255)

    @property
    def publish_function(self):
        model = getattr(
            importlib.import_module(self.model_module),
            self.model_class
        )
        return getattr(model, self.name)


class Subscription(models.Model):
    '''
    A subscription is an object representing the relation between
    a client and a publication. It also stores the id of the component
    that subscribes to a given publication, and the queryset
    computed from that publication query. This queryset is computed
    per-subscription to permit user specific sets
    After being instanciated, a subscription must be initialized by
    it's init() method so that it fills the component asking for it
    by its content via ryzom.ddp send_insert.
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, models.CASCADE, blank=True, null=True)
    publication = models.ForeignKey(Publication, models.CASCADE)
    subscriber_id = models.CharField(max_length=255)
    subscriber_module = models.CharField(max_length=255)
    subscriber_class = models.CharField(max_length=255)
    queryset = ArrayField(models.IntegerField(), default=list)
    options = JSONField(blank=True, null=True)

    @property
    def subscriber(self):
        subscriber_mod = importlib.import_module(self.subscriber_module)
        return getattr(subscriber_mod, self.subscriber_class)

    def get_queryset(self, opts=None):  # noqa: C901
        '''
        This method computes the publication query and create/update the
        queryset for the current subscription.
        It supports somme special variables such as $count and $user that
        are parsed and replaced with, respectively, the queryset.count()
        value and the current user associated with the subscription client
        More will come with special variables and function. Such as an $add
        to replace that ugly tupple i'm using for now.. to be discussed
        '''

        queryset = self.publication.publish_function(self.client.user)

        opts = opts or self.options
        queryset = self.subscriber.get_queryset(
            self.client.user, queryset, opts)

        self.options = opts
        self.queryset = list(queryset.values_list('id', flat=True))
        self.save()

        return queryset
