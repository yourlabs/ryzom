"""Facet reverse-matching unit tests (PROBLEM.md step 3 / MATCHING.md).

These are pure-Python (no DB) and pin the regression where a freshly created
instance holds raw form strings (e.g. stock_qty="5"), which BooleanFacet then
compared against an int.
"""
import pytest
from django.conf import settings

skip_reactive = pytest.mark.skipif(
    not settings.CHANNELS_ENABLE, reason='Reactive disabled')


@skip_reactive
def test_snapshot_coerces_form_strings():
    from ryzom_django_channels.signals import _snapshot
    from ryzom_example_crud.models import Product

    # ProductCreateView builds the instance from request.POST strings; the
    # snapshot used for reverse matching must coerce to the field's type.
    snap = _snapshot(Product(name='X', price='1.50', stock_qty='5'))
    assert snap['stock_qty'] == 5 and isinstance(snap['stock_qty'], int)


@skip_reactive
def test_boolean_facet_candidate_handles_string_instance():
    from ryzom_django_channels.facets import BooleanFacet
    from ryzom_django_channels.signals import _snapshot
    from ryzom_example_crud.models import Product

    facet = BooleanFacet('in_stock', 'stock_qty')  # "on" => stock_qty > 0
    # Regression: must not raise on a string-valued (uncoerced) instance.
    _a, q_in = facet.candidate(_snapshot(Product(stock_qty='5')))
    _a, q_out = facet.candidate(_snapshot(Product(stock_qty='0')))
    # in range => no constraint (every sub admits it); out of range => only
    # subs that did not switch the flag on.
    assert not q_in.children
    assert q_out.children


@skip_reactive
def test_search_facet_candidate_builds_reverse_predicate():
    from ryzom_django_channels.facets import SearchFacet

    ann, q = SearchFacet('q', 'name').candidate({'name': 'Widget'})
    assert '_match_q' in ann
    assert ('_match_q__gt', 0) in q.children
