"""
URL wiring for the reactive Product demo.

Everything reactive now lives in the declarative ``ProductCrud``
(``components.py``) on top of the generic ``ReactiveRouter``; this module just
mounts it. The ``ProductListView`` / ``ProductBulkView`` aliases expose the
generated view classes for the test suite.
"""
from ryzom_example_crud.components import ProductCrud

urlpatterns, app_name = ProductCrud.get_urls()

# Named handles onto the generated views (used by tests / external references).
ProductListView = ProductCrud.views['list']
ProductDetailView = ProductCrud.views['detail']
ProductCreateView = ProductCrud.views['create']
ProductBulkView = ProductCrud.views['bulk']
