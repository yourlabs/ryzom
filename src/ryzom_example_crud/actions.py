"""
Generic action registry for the live Product table.

The selection/menu UI is generic; the *actions* are pluggable — anything
decorated with ``@action`` becomes an entry the toolbar (bulk) and/or the
per-row kebab menu offers. A handler receives the already-resolved queryset
(the selected rows, or a single row for a per-row action) plus the ``request``,
and mutates it **per object** so the Publishable post_save/post_delete signals
fire and every connected client's table updates over DDP — the same push path
the Sell button relies on. (``.update()`` / bulk ``QuerySet.delete()`` are
avoided on purpose: they would skip the per-row signals and live tables would
not refresh.)

An action can opt into an **interaction**: a confirmation message and/or input
fields. When it does, the client opens a server-rendered ``MDCDialog`` (see
ActionDialog in components.py) before running it; the dialog's inputs arrive as
ordinary POST params, so a handler just reads ``request.POST[...]``.

Each action also declares its **scopes** — where it may appear:
``'bulk'`` (the selection toolbar) and/or ``'row'`` (the per-row kebab menu).
``rename`` is row-only on purpose: renaming many rows to one name is nonsense.

Adding an action is one decorated function; nothing else changes.
"""
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Field:
    """One input rendered inside an action's dialog."""
    name: str
    label: str
    type: str = 'text'
    required: bool = False


@dataclass
class Action:
    slug: str
    label: str
    fn: Callable
    confirm: str = None           # confirmation message (None => no message)
    fields: tuple = ()            # input Fields collected before running
    scopes: tuple = ('bulk',)     # 'bulk' (toolbar) and/or 'row' (kebab menu)

    @property
    def interactive(self):
        """True when running this action requires a dialog (confirm or input)."""
        return bool(self.confirm or self.fields)


# slug -> Action
ACTIONS = {}


def action(slug, label, *, confirm=None, fields=None, scopes=('bulk',)):
    """Register ``fn`` as an action under ``slug`` (shown as ``label``).

    ``confirm``/``fields`` make it interactive (a dialog opens first);
    ``scopes`` picks where it shows up ('bulk' toolbar and/or 'row' menu).
    """
    def register(fn):
        ACTIONS[slug] = Action(
            slug, label, fn,
            confirm=confirm,
            fields=tuple(fields or ()),
            scopes=tuple(scopes),
        )
        return fn
    return register


def actions_for(scope):
    """The registered actions available in a given scope ('bulk' or 'row')."""
    return [a for a in ACTIONS.values() if scope in a.scopes]


@action('delete', 'Delete', scopes=('bulk', 'row'),
        confirm='Permanently delete the selected product(s)? '
                'This cannot be undone.')
def _delete(queryset, request):
    # Per-object delete so each fires post_delete -> a DDP remove on every list.
    for obj in queryset:
        obj.delete()


@action('rename', 'Rename', scopes=('row',),
        fields=[Field('name', 'New name', required=True)])
def _rename(queryset, request):
    # Row-only: the dialog ships a single new name; apply it to the one row.
    name = (request.POST.get('name') or '').strip()
    if not name:
        return
    for obj in queryset:
        obj.name = name
        obj.save()  # post_save -> DDP change push


@action('restock', 'Restock (+10)', scopes=('bulk', 'row'))
def _restock(queryset, request):
    for obj in queryset:
        obj.stock_qty += 10
        obj.save()  # post_save -> DDP change push


@action('out_of_stock', 'Mark out of stock', scopes=('bulk',))
def _out_of_stock(queryset, request):
    for obj in queryset:
        obj.stock_qty = 0
        obj.save()
