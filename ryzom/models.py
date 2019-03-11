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
