"""
Reactive CRUD demo model.

Product subclasses Publishable so that save()/delete() fire the channels DDP
signals — every connected subscriber's queryset is diffed and insert / change /
remove messages are pushed over the websocket. The @publish method registers a
named publication ('products') that components subscribe to.
"""
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from ryzom_django_channels.pubsub import Publishable, publish


class Product(Publishable, models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_qty = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @publish
    def products(cls, user):
        return cls.objects.all()


@receiver(post_save, sender=Product)
def _refresh_product_detail(sender, instance, **kwargs):
    """Push a fresh render to any open detail view for this product.

    The channels publication signals only update *list* subscriptions; the
    single-object detail view is a registered ReactiveComponent, so we refresh
    it explicitly here. No-op when nobody is viewing this product's detail.
    """
    from ryzom_django_channels.views import register
    register(f'product-detail-{instance.pk}').refresh(instance)
