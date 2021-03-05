'''
This file defines the models needed for ryzom pub/sub system.
They're not intended to be used by end-user.
'''
import importlib
import secrets
import uuid

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import JSONField


class Clients(models.Model):
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
    template_module = models.CharField(max_length=255)
    template_class = models.CharField(max_length=255)

    def get_model(self):
        return self._import(self.model_module, self.model_class)

    def get_template(self):
        return self._import(
                self.template_module,
                self.template_class)

    def _import(self, mod, cls):
        return getattr(importlib.import_module(mod), cls)


class Subscription(models.Model):
    '''
    A subscription is an object representing the relation between
    a client and a publication. It also stores the _id of the component
    that subscribes to a given publication, and the queryset
    computed from that publication query. This queryset is computed
    per-subscription to permit user specific sets
    After being instanciated, a subscription must be initialized by
    it's init() method so that it fills the component asking for it
    by its content via ryzom.ddp send_insert.
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Clients, models.CASCADE, blank=True, null=True)
    publication = models.ForeignKey(Publication, models.CASCADE)
    subscriber_module = models.CharField(max_length=255)
    subscriber_class = models.CharField(max_length=255)
    queryset = ArrayField(models.IntegerField(), default=list)
    options = JSONField(blank=True, null=True)


    def init(self, opts):
        '''
        This method is used to populate the component which made
        the current subsription with its content, and to compute
        the queryset for the first time.
        This part is subject to near changes when SSR will be
        implemented
        '''
        from ryzom.ddp import send_insert

        self.get_queryset(opts)

        model = self.publication.get_model()
        template = self.publication.get_template()

        for _id in self.queryset:
            send_insert(self, model, template, _id)

    def get_queryset(self, opts={}):  # noqa: C901
        '''
        This method computes the publication query and create/update the
        queryset for the current subscription.
        It supports somme special variables such as $count and $user that
        are parsed and replaced with, respectively, the queryset.count()
        value and the current user associated with the subscription client
        More will come with special variables and function. Such as an $add
        to replace that ugly tupple i'm using for now.. to be discussed
        '''
        model = self.publication.get_model()

        subscriber_mod = importlib.import_module(self.subscriber_module)
        subscriber_class = getattr(sub_mod, self.subscriber_class)

        publish_fonction = getattr(model, pub.name)

        queryset = publish_function(user)

        try:
            sub_get_queryset = getattr(subscriber_class, 'get_queryset')
        except AttributeError:
            pass
        else:
            queryset = sub_get_queryset(queryset, opts)

        self.options = opts
        self.queryset = queryset.aggregate(ids=ArrayAgg('id'))['id']
        self.save()

        return queryset
