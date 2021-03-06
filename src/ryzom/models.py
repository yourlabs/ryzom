'''
This file defines the models needed for ryzom pub/sub system.
They're not intended to be used by end-user.
'''
import importlib
import secrets

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from django.contrib.postgres.aggregates import ArrayAgg


class Tokens(models.Model):
    '''
    '''
    token = models.CharField(default=secrets.token_urlsafe,
                             max_length=255, unique=True)
    user = models.OneToOneField(User, models.CASCADE)


class Clients(models.Model):
    '''
    Clients are the representation of connected Clients
    over websockets. It stores the channel name of a single
    client to communicate over the channel layer
    The user field is not used for now but in a near future
    it will be used to store the user using this channel
    once it's connected
    '''
    channel = models.CharField(max_length=255)
    user = models.ForeignKey(
                User,
                models.SET_NULL,
                blank=True,
                null=True
           )


class Publications(models.Model):
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
    query = JSONField(blank=True, null=True)


class Subscriptions(models.Model):
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
    parent = models.CharField(max_length=255)
    client = models.ForeignKey(Clients, models.CASCADE)
    publication = models.ForeignKey(Publications, models.CASCADE)
    queryset = ArrayField(models.IntegerField(), default=list)

    def init(self):
        '''
        This method is used to populate the component which made
        the current subsription with its content, and to compute
        the queryset for the first time.
        This part is subject to near changes when SSR will be
        implemented
        '''
        from ryzom.ddp import send_insert
        pub = self.publication
        model_mod = importlib.import_module(pub.model_module)
        model_cls = getattr(model_mod, pub.model_class)
        tmpl_mod = importlib.import_module(pub.template_module)
        tmpl_cls = getattr(tmpl_mod, pub.template_class)
        qs = self.exec_query(model_cls).aggregate(ids=ArrayAgg('id'))
        self.queryset = qs['ids']
        for _id in self.queryset:
            send_insert(self, model_cls, tmpl_cls, _id)

    def exec_query(self, model):  # noqa: C901
        '''
        This method computes the publication query and create/update the
        queryset for the current subscription.
        It supports somme special variables such as $count and $user that
        are parsed and replaced with, respectively, the queryset.count()
        value and the current user associated with the subscription client
        More will come with special variables and function. Such as an $add
        to replace that ugly tupple i'm using for now.. to be discussed
        '''
        # such an ugly code!
        # I really have to makes this clearer...and more robust!
        # but it works for now
        pub = self.publication
        qs = model.objects.all()
        for q in pub.query:
            for k, v in q.items():
                if isinstance(v, list):
                    if v[0] == '$count':
                        v[0] = qs.count()
                        v = max(v[0] + v[1], 0)
                    elif v[0] == '$user':
                        v[0] = self.client.user.id
                elif isinstance(v, dict):
                    for _k, _v in v.values():
                        if _v == '$user':
                            v[_k] = self.client.user.id
                if k == 'filter':
                    qs = qs.filter(**v)
                elif k == 'order_by':
                    qs = qs.order_by(v)
                elif k == 'limit':
                    qs = qs[:v]
                elif k == 'offset':
                    qs = qs[v:]
        return qs
