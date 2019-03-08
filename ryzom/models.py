import importlib

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from django.contrib.postgres.aggregates import ArrayAgg
from ryzom.ddp import send_insert


class Clients(models.Model):
    channel = models.CharField(max_length=255)
    user = models.ForeignKey(
                User,
                models.SET_NULL,
                blank=True,
                null=True
           )


class Publications(models.Model):
    name = models.CharField(max_length=255, unique=True)
    model_module = models.CharField(max_length=255)
    model_class = models.CharField(max_length=255)
    template_module = models.CharField(max_length=255)
    template_class = models.CharField(max_length=255)
    query = JSONField(blank=True, null=True)


class Subscriptions(models.Model):
    parent = models.CharField(max_length=255)
    client = models.ForeignKey(Clients, models.CASCADE)
    publication = models.ForeignKey(Publications, models.CASCADE)
    queryset = ArrayField(models.IntegerField(), default=list)

    def init(self):
        pub = self.publication
        model_mod = importlib.import_module(pub.model_module)
        model_cls = getattr(model_mod, pub.model_class)
        tmpl_mod = importlib.import_module(pub.template_module)
        tmpl_cls = getattr(tmpl_mod, pub.template_class)
        qs = self.exec_query(model_cls).aggregate(ids=ArrayAgg('id'))
        self.queryset = qs['ids']
        for _id in self.queryset:
            send_insert(self, model_cls, tmpl_cls, _id)

    def exec_query(self, model):
        '''
        limit, orderby, offset, fields(values), filter
        '''
        pub = self.publication
        qs = model.objects.filter(**pub.query.get('filter', {}))
        if 'order_by' in pub.query:
            qs = qs.order_by(*pub.query.order_by)
        if 'limit' in pub.query or 'offset' in pub.query:
            limit = pub.query.get('limit')
            offset = pub.query.get('offset', 0)
            if limit:
                qs = qs[offset:offset + limit]
            else:
                qs = qs[offset:]
        return qs
