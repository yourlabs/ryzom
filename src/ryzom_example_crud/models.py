"""
Reactive CRUD demo model.

Product subclasses Publishable so that save()/delete() fire the channels DDP
signals — every connected subscriber's queryset is diffed and insert / change /
remove messages are pushed over the websocket. The @publish method registers a
named publication ('products') that components subscribe to.
"""
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from ryzom_django_channels.pubsub import Publishable, publish


class Product(Publishable, models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_qty = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    # Per-user visibility (see GroupFacet): a row visible to its group's members
    # (+ staff); NULL means public. A single FK (not M2M) keeps the visibility
    # key a concrete column so it lands in the reverse-matching snapshot.
    group = models.ForeignKey(
        'auth.Group', models.SET_NULL, null=True, blank=True,
        related_name='products',
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @publish
    def products(cls, user):
        # The visibility predicate lives in GroupFacet (forward), applied by
        # SubscribeComponentMixin.get_queryset; this stays the unscoped base.
        return cls.objects.all()


class LiveUser(Publishable, User):
    """A Publishable proxy of ``auth.User`` so the generic reactive CRUD can
    drive the User list live.

    The reactive push routes a save to its publication by the *saved instance's*
    class (see ryzom_django_channels.signals): only instances whose class has
    ``Publishable`` in its MRO push. The CRUD's create/update/delete go through
    this proxy, so they push; plain ``auth.User`` saves (login, admin) don't —
    which is the intended scope for the demo.
    """
    class Meta:
        proxy = True
        verbose_name = 'user'
        verbose_name_plural = 'users'

    @publish
    def users(cls, user):
        return cls.objects.all()


@receiver(post_save, sender=LiveUser)
def _refresh_user_detail(sender, instance, **kwargs):
    """Push a fresh render to any open detail view for this user (the list
    subscriptions update themselves; a single-object detail is a Registration)."""
    from ryzom_django_channels.views import register
    register(f'liveuser-detail-{instance.pk}').refresh(instance)


@receiver(post_save, sender=Product)
def _refresh_product_detail(sender, instance, **kwargs):
    """Push a fresh render to any open detail view for this product.

    The channels publication signals only update *list* subscriptions; the
    single-object detail view is a registered ReactiveComponent, so we refresh
    it explicitly here. No-op when nobody is viewing this product's detail.
    """
    from ryzom_django_channels.views import register
    register(f'product-detail-{instance.pk}').refresh(instance)
