'''
This file defines the models needed for ryzom pub/sub system.
They're not intended to be used by end-user.
'''
import importlib
import secrets
import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
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
    subscriber_module = models.CharField(max_length=255)
    subscriber_class = models.CharField(max_length=255)

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
    def model(self):
        return getattr(
            importlib.import_module(self.model_module),
            self.model_class
        )

    @property
    def publish_function(self):
        return getattr(self.model, self.name)


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
    qs = ArrayField(models.CharField(max_length=255), default=list)
    options = JSONField(blank=True, null=True)

    @property
    def subscriber(self):
        subscriber_mod = importlib.import_module(self.subscriber_module)
        return getattr(subscriber_mod, self.subscriber_class)

    @property
    def queryset(self):
        return [
            self.publication.model.id.field.to_python(i)
            for i in self.qs
        ]

    @queryset.setter
    def queryset(self, value):
        self.qs = [str(i) for i in value]

    def row_queryset(self, opts=None):
        '''The subscriber's filtered, totally-ordered queryset, *unsliced*.

        Used by the DDP signal handlers to fetch row instances by pk (a sliced
        queryset can't be ``.get(pk=...)``'d) while preserving any annotations
        the subscriber added.
        '''
        opts = opts if opts is not None else (self.options or {})
        base = self.publication.publish_function(self.client.user)
        qs = self.subscriber.get_queryset(self.client.user, base, opts)
        order = getattr(self.subscriber, 'order', None)
        if order:
            qs = qs.order_by(*order)
        return qs

    def get_queryset(self, opts=None):  # noqa: C901
        '''
        Compute the subscription's queryset and persist its id list.

        Pagination is opt-in: when the subscriber declares ``paginate_by`` (and
        a total ``order``), the stored ``qs`` is just the visible *window*
        (``[offset:offset+per_page]``) and ``options`` is updated with the
        clamped ``offset``/``per_page``, the ``total`` count, and the
        ``first_key``/``last_key`` sort tuples. Subscribers without
        ``paginate_by`` keep the previous behaviour (the whole filtered set).
        '''
        opts = dict(opts if opts is not None else (self.options or {}))
        queryset = self.row_queryset(opts)

        paginate_by = getattr(self.subscriber, 'paginate_by', None)
        if not paginate_by:
            self.options = opts
            self.queryset = queryset.values_list('id', flat=True)
            self.save()
            return queryset

        order = getattr(self.subscriber, 'order', ('id',))
        per_page = max(1, int(opts.get('per_page') or paginate_by))
        total = queryset.count()

        # Clamp the offset onto a real page (deletes may have shrunk the set).
        last_offset = ((total - 1) // per_page) * per_page if total else 0
        offset = min(max(0, int(opts.get('offset') or 0)), last_offset)

        window = list(queryset[offset:offset + per_page])
        opts.update(
            per_page=per_page,
            offset=offset,
            total=total,
            first_key=self._order_key(window[0], order) if window else None,
            last_key=self._order_key(window[-1], order) if window else None,
        )
        self.options = opts
        self.queryset = [obj.id for obj in window]
        self.save()
        return window

    @staticmethod
    def _order_key(obj, order):
        '''The row's sort-key tuple as a JSON-storable list, e.g. [name, id].

        Compared as a list against another row's key for the boundary skip, so
        the order fields must be JSON-serialisable and mutually comparable
        (str/int/bool). ``('name', 'id')`` satisfies this.
        '''
        return [getattr(obj, field) for field in order]
