---
name: create-component
description: Create a Ryzom component (a Python class that renders HTML) — plain, or reactive/live over channels. Use when asked to add/build/write a component, widget, page, row, form, or live/reactive list/detail in this project. Explains the patterns and gives templates to copy.
---

# Create a Ryzom component

Ryzom renders **Python objects to HTML** — no templates. A component is a class
that builds a tree of other components/elements. Build trees from the MDC html
namespace; positional args are children, keyword args are HTML attributes.

```python
from ryzom_django_mdc.html import *   # Div, Span, A, H1, Input, Select, MDC* …
```

Canonical, real examples to read before writing: `src/ryzom_example_crud/components.py`
(reactive list + row + form + detail) and `src/ryzom_mdc/html.py` (the widget
library). Background: `docs/design/SYNTHESIS.md`.

## 1. Plain component

```python
class PriceTag(Component):
    def __init__(self, product):
        super().__init__(
            Span(product.name),
            Span(f'${product.price}', style='font-weight:bold'),
            cls='price-tag',          # -> class="price-tag"
        )
```

Use it anywhere as a child: `Div(PriceTag(p), ...)`. A view renders a tree with
`HttpResponse(doc.to_html(view=self))` (see `views.py`).

## 2. Reactive list — a subscribed `<tbody>` + a pushed row

The list subscribes to a publication; the server pushes insert/change/remove ops
for individual rows. Two pieces:

```python
from ryzom_django_channels.components import (
    SubscribeComponentMixin, model_template,
)

# (a) the row — the unit the server pushes. The decorator name is the template id.
@model_template('product-row')
class ProductRow(MDCDataTableTr):
    def __init__(self, obj):
        super().__init__(
            MDCDataTableTd(A(obj.name, href=f'/crud/products/{obj.id}/')),
            MDCDataTableTd(f'${obj.price}'),
            data_id=obj.id,
        )

# (b) the subscribed container — declares the publication + its facets
class ProductRows(SubscribeComponentMixin, MDCDataTableTbody):
    publication = 'products'
    model_template = 'product-row'
    facets = [SearchFacet('q', ['name']), GroupFacet(field='group')]
```

`facets` (in `ryzom_django_channels/facets.py`) express filtering/visibility
**once**, used both forward (scope the queryset) and reverse (route a write to
the subscriptions it affects). See `docs/design/MATCHING.md` / `PROBLEM.md` before
adding a new facet.

## 3. Reactive detail — re-rendered on every change

```python
from ryzom_django_channels.components import ReactiveComponentMixin

class ProductDetail(ReactiveComponentMixin, Component):
    register = 'product-detail'        # registration id used to re-render on save
    def __init__(self, obj):
        super().__init__(H1(obj.name), Div(f'In stock: {obj.stock_qty}'))
```

## 4. Wire it up

- Put components in the app's `components.py`.
- Render from a `View` in `views.py`; add the route to that module's
  `urlpatterns` (the crud demo is mounted at `/crud/products/` in
  `src/ryzom_django_example/urls.py`).
- Reactive pages mix in `ReactiveMixin` and call `self.get_token()` to emit the
  config `<meta>` the client JS reads (transport, poll url, token).

## After writing

- `ruff check src` and `python -m pytest -q` (use the **run-tests** skill).
- See it live with the **run-demo** skill; for a model change add a migration
  (`python manage.py makemigrations && migrate`).
