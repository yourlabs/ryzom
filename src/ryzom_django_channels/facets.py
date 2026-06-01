"""
Declarative filter facets for reactive subscriptions.

A facet expresses one filter parameter in two directions from a *single*
definition (the "express the predicate once" goal in PROBLEM.md §6/§9):

- ``forward(queryset, value)`` — apply this subscription's stored value to the
  data queryset. This is the single source of truth for the filter, used to
  render and window the list.
- ``candidate(row)`` — the reverse: an ``(annotations, Q)`` pair over the
  *Subscription* table selecting the subscriptions whose stored value would
  include ``row``. This lets a single row change be routed to only the
  subscriptions it can affect (PROBLEM.md step 3 / §3 "reverse query"), instead
  of re-running every standing query.

``row`` is a plain dict of the changed object's field values (a snapshot), so
the reverse test never touches the live instance.

A subscription is a *candidate* for a change to row X iff X matches its filter
with X's new values OR its old values (see MATCHING.md): the window is
irrelevant to candidacy, because a window is a slice of the filtered set and a
row outside the set, before and after, cannot change any window over it.
"""
from django.db.models import Q, Value
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Coalesce, Lower, StrIndex


class Facet:
    def __init__(self, key):
        # the Subscription.options key holding this facet's per-client value
        self.key = key

    def forward(self, queryset, value):
        raise NotImplementedError

    def candidate(self, row):
        """(annotations, Q) selecting Subscriptions whose stored value for this
        facet admits ``row``. Default: no constraint (admits every row)."""
        return {}, Q()


class BooleanFacet(Facet):
    """A flag that, when truthy, keeps only rows with ``field > gt``
    (e.g. ``in_stock`` -> ``stock_qty > 0``).

    Reverse: a row that is in range is admitted by *every* subscription; a row
    out of range is admitted only by subscriptions that did not switch the flag
    on (a subscription with the flag off has no opinion about it).
    """
    def __init__(self, key, field, gt=0):
        super().__init__(key)
        self.field = field
        self.gt = gt

    def forward(self, queryset, value):
        if value:
            return queryset.filter(**{f'{self.field}__gt': self.gt})
        return queryset

    def candidate(self, row):
        value = row.get(self.field)
        in_range = value is not None and value > self.gt
        if in_range:
            return {}, Q()
        return {}, ~Q(**{f'options__{self.key}': True})


class SearchFacet(Facet):
    """A case-insensitive substring search over ``field`` (``field ILIKE
    %term%``).

    Reverse: a subscription admits the row iff its stored term is a substring of
    the row's field value (``strpos(row_value, term) > 0``); an empty/missing
    term matches everything (``strpos(x, '') = 1``). This is a sequential scan
    over the subscription table's stored terms — the cheap, un-indexed end of
    PROBLEM.md §5; an inverted index / trie over terms is the heavy version,
    deferred. It is still one in-DB scan of the (small) subscription table, not
    a requery of the data table per subscription.
    """
    def __init__(self, key, field):
        super().__init__(key)
        self.field = field

    def forward(self, queryset, value):
        value = (value or '').strip()
        if value:
            return queryset.filter(**{f'{self.field}__icontains': value})
        return queryset

    def candidate(self, row):
        alias = f'_match_{self.key}'
        # stored term (lower-cased, '' when absent) as the needle; the changed
        # row's field value as the haystack constant.
        term = Coalesce(Lower(KeyTextTransform(self.key, 'options')), Value(''))
        haystack = Value((row.get(self.field) or '').lower())
        return {alias: StrIndex(haystack, term)}, Q(**{f'{alias}__gt': 0})
