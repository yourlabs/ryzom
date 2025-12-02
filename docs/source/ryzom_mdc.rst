Material Design components (``ryzom_mdc.html``)
===============================================

``ryzom_mdc.html`` exposes Material Design Components (MDC) as Python classes
so you can build interfaces without hand-writing MDC HTML. This reference lists
the available pieces and how to use them, so you can build pages without
reading the source.

General tips
------------

- All components accept standard ryzom attributes (``id``, ``addcls``,
  ``style``, ``data-*``). Icon arguments accept either a string (material icon
  name) or any component.
- MDC JS/CSS is not bundled here; include it once in your base template and
  MDC’s auto-init will pick up the ``data-mdc-auto-init`` markers rendered by
  these components.

Buttons and links
-----------------

- ``MDCButton(text=None, icon=None, **attrs)``: Base text button. Works as
  ``<button>`` or ``<a>`` depending on ``tag``/``href`` or ``type`` attrs.
- ``MDCButtonRaised(...)``: Adds ``mdc-button--raised``.
- ``MDCButtonOutlined(...)``: Adds ``mdc-button--outlined``.
- ``MDCTextButton(...)``: Text-only style with ripple.
- ``MDCButtonLabelOutlined(text, p=True, icon=None, **attrs)``: An outlined
  button rendered as a ``<label>``; handy to trigger hidden file inputs.
- ``MDCLink``: Minimal wrapper over ``A`` for MDC styling when needed.

Icons and chips
---------------

- ``MDCIcon(name, **attrs)``: Renders a material icon with the correct class
  and ``aria-hidden`` by default.
- Chip helpers live in this module too (``MDCChip`` and friends) and mirror the
  MDC deprecated chip API; they accept leading/trailing icons, text, and ripple
  flags.

Text inputs
-----------

- ``MDCTextInput(name, **attrs)``: Plain input with MDC class; defaults to type
  ``text``.
- ``MDCTextFieldOutlined(html_input, label=None, help_text=None, errors=None,
  licon=None, ticon=None, suffix=None, **attrs)``: Outlined field wrapper with
  floating label, helper, error wiring, leading/trailing icons, optional suffix
  text. Floats the label automatically if a value is present.
- ``MDCTextareaFieldOutlined(textarea, ...)``: Same API as the outlined text
  field but wraps a ``Textarea`` and adds the MDC resizer.
- ``MDCField(*content, name, label=None, help_text=None, errors=None, **attrs)``:
  Base field container that positions helper/error text with consistent
  vertical spacing.
- ``MDCFormField(*content, name, label=None, help_text=None, errors=None, **attrs)``:
  Simpler container often used to wrap checkboxes or custom controls alongside
  helper/error text.

Supporting pieces for text fields (usually not instantiated directly):
``MDCLabel``, ``MDCTextRipple``, ``MDCLineRipple``, ``MDCNotchOutline``.

Checkboxes, switches, multi-choice
----------------------------------

- ``MDCCheckboxInput(input=None, **attrs)``: Checkbox shell; wraps a native
  checkbox (or a custom ``input``) with MDC checkmark graphics.
- ``MDCCheckboxRadioInput(...)``: Checkbox shell with radio-like visual.
- ``MDCCheckboxField(input, name, label=None, help_text=None, errors=None)``:
  Full checkbox field with label and helper/error text.
- ``MDCCheckboxSelectField(*content, name, ...)``: Container variant used when
  multiple checkboxes are displayed together.
- ``MDCCheckboxListItem(title, id, checked=False, **input_attrs)``: List item
  with a checkbox graphic and label; clicking the row toggles the checkbox.
- ``MDCMultipleChoicesCheckbox(name, choices, n=1, **input_attrs)``: Generates
  a list of ``MDCCheckboxListItem`` and enforces a maximum of ``n`` checked
  items by disabling unchecked entries when the limit is reached.
- Switches: ``MDCSwitchInput``, ``MDCSwitch`` and related helpers provide the
  MDC switch markup; pass ``checked`` to set initial state.

Selects and options
-------------------

- ``MDCOption`` / ``MDCOptionMixin`` / ``MDCOptgroup`` / ``MDCNamedOptgroup``:
  Helpers to render option rows and optgroups (with or without group headers).
- ``MDCSelectMenu(optgroups, **attrs)``: Menu container holding option lists.
- ``MDCSelectAnchor(label, selected=None, **attrs)``: The clickable anchor with
  notched outline, selected text and dropdown icon.
- ``MDCSelect(select, **attrs)``: Convenience wrapper to render a filled select
  from a ``Select`` element’s children.
- ``MDCSelectOutlined(**context)``: Outlined select (label + anchor + menu)
  intended to mimic the Django select widget; accepts ``label`` plus the
  ``optgroups`` structure.

Lists and tables
----------------

- ``MDCList``: Deprecated MDC list container; auto-inits ``MDCList`` JS.
- ``MDCListItem(*content, icon=None, meta=None, ripple=True, **attrs)``:
  Standard list row with optional leading icon, trailing meta, and ripple
  toggle.
- Data table helpers: ``MDCDataTable`` (container), ``MDCDataTableHead``,
  ``MDCDataTableBody``, ``MDCDataTableRow``, ``MDCDataTableTh``, and
  ``MDCDataTableTd`` (render ``<tr>/<th>/<td>`` with MDC classes). Use them to
  build sortable or reactive tables.

Feedback and utility components
-------------------------------

- ``MDCSnackBar(msg, status='success', delay=0)``: Snackbar with message and
  action button. Opens automatically when connected.
- ``MDCErrorList(*errors)`` / ``MDCErrorListItem``: Compact red error text list
  suitable under form fields.
- ``MDCHelpText(text, **attrs)``: Grey caption-sized helper text.
- ``MDCVerticalMargin``: Spacer div with preset top/bottom margins.
- ``MDCFileField(input, label=None, help_text=None, errors=None, **attrs)``:
  Hidden file input plus a stylable label button and filename display; includes
  JS to update the label when a file is chosen.
- ``MDCSplitDateTime(name=..., value=None, **attrs)``: Two outlined inputs
  (date and time) combined under one container; exposes ``set_error`` to mark
  the field invalid and display helper text.

Data entry extras
-----------------

- ``MDCSelectOutlined`` and ``MDCSelect`` provide select dropdowns; use
  ``MDCOption`` or ``MDCOptgroup`` to source the choices.
- ``MDCTextFieldHelperText`` / ``MDCTextFieldHelperLine``: Low-level helper
  containers used inside fields.

Using the components
--------------------

1. Include MDC JS/CSS in your page.
2. Import needed components from ``ryzom_mdc.html``.
3. Compose UI as Python objects; pass standard HTML attributes and optional
   icons/content.
4. For forms, wrap inputs in ``MDCTextFieldOutlined`` or the checkbox/select
   helpers to get labels and validation styling; use ``MDCErrorList`` for
   server-side errors.

Working examples
----------------

Data table with pagination
~~~~~~~~~~~~~~~~~~~~~~~~~~

Combining the data-table helpers produces a fully structured MDC table that
auto-inits client-side sorting, selection, and pagination::

    from ryzom_mdc.html import (
        MDCDataTable, MDCDataTableTable, MDCDataTableThead, MDCDataTableTh,
        MDCDataTableTbody, MDCDataTableTr, MDCDataTableTd,
        MDCDataTablePagination, MDCButton, MDCSelectOutlined, MDCOption
    )

    header = MDCDataTableThead(
        MDCDataTableTh('Name'),
        MDCDataTableTh('Status'),
        MDCDataTableTh('Owner'),
    )
    body = MDCDataTableTbody(
        MDCDataTableTr(
            MDCDataTableTd('Foo'),
            MDCDataTableTd('Active'),
            MDCDataTableTd('Alice'),
        ),
        MDCDataTableTr(
            MDCDataTableTd('Bar'),
            MDCDataTableTd('Paused'),
            MDCDataTableTd('Bob'),
        ),
    )
    pagination = MDCDataTablePagination(
        rows_per_page_select=MDCSelectOutlined(
            label='Rows per page',
            optgroups=[(None, [
                dict(label='10', value='10', selected=True),
                dict(label='25', value='25'),
                dict(label='50', value='50'),
            ], 0)],
        ),
        page_label='1 of 5',
        next_button=MDCButton('Next', icon='chevron_right', tag='button'),
        prev_button=MDCButton('Prev', icon='chevron_left', tag='button'),
    )

    table = MDCDataTable(
        table=MDCDataTableTable(thead=header, tbody=body),
        pagination=pagination,
    )

Drop ``table`` into your page; MDC JS will enhance it (keyboard nav, responsive
layout if you wrap it in ``MDCDataTableResponsive``).

Dialog with actions
~~~~~~~~~~~~~~~~~~~

Dialogs are composed from smaller parts; the high-level ``MDCDialog`` accepts
content and actions and wires the MDC dialog lifecycle::

    from ryzom_mdc.html import (
        MDCDialog, MDCDialogActions, MDCDialogTitle, MDCDialogContent,
        MDCDialogAcceptButton, MDCDialogCloseButtonOutlined
    )

    dialog_body = MDCDialogContent(
        P('Are you sure you want to archive this project?')
    )
    actions = MDCDialogActions(
        MDCDialogCloseButtonOutlined('Cancel', type='button'),
        MDCDialogAcceptButton('Archive', type='button'),
    )
    dialog = MDCDialog(
        MDCDialogTitle('Confirm archive'),
        dialog_body,
        actions=actions,
        modal=True,
    )

The dialog auto-inits on connect. You can attach JS listeners for
``MDCDialog:opened`` / ``:closed`` by adding methods to the embedded HTMLElement
class if you need to hook into lifecycle events.

Select with optgroups
~~~~~~~~~~~~~~~~~~~~~

``MDCSelectOutlined`` can render grouped options and a label in one call::

    from ryzom_mdc.html import MDCSelectOutlined

    country_select = MDCSelectOutlined(
        label='Country',
        optgroups=[
            ('Europe', [
                dict(label='France', value='fr'),
                dict(label='Germany', value='de'),
            ], 0),
            ('Americas', [
                dict(label='Canada', value='ca'),
                dict(label='United States', value='us', selected=True),
            ], 1),
        ],
        name='country',
        required=True,
    )

This renders the notched outline, selected text, and full-width menu ready for
MDC JS to enhance; the ``selected`` flag sets the initial value.

Chip sets and snackbar queue
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Quick reusable snippets:

- Chips::

    from ryzom_mdc.html import MDCChip

    chip_bar = Div(
        MDCChip('Draft', licon='article'),
        MDCChip('Published', licon='public', selected=True),
        MDCChip('Archived', licon='inventory_2'),
        cls='chip-bar',
    )

- Snackbar queue (multiple messages that show sequentially)::

    messages = ['Saved', 'Indexing started', 'Report ready']
    snackbars = [MDCSnackBar(msg, delay=i * 4000) for i, msg in enumerate(messages)]
    alerts = Div(*snackbars)

Reactive paginated data table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To pair MDC tables with live data over websockets, combine the table helpers
with ``SubscribeComponentMixin`` from ``ryzom_django_channels``. The component
subscribes to a publication, renders row components registered via
``@model_template``, and exposes pagination controls that update
``subscribe_options``.

Example: a reactive table of tasks with server-side pagination (rows rendered by
``TaskRow``, pagination state stored in ``subscribe_options``, page label updated
from ``options`` set in ``get_queryset``)::

    from ryzom_django_channels.components import (
        SubscribeComponentMixin, model_template
    )
    from ryzom_mdc.html import (
        MDCDataTable, MDCDataTableTable, MDCDataTableThead, MDCDataTableTh,
        MDCDataTableTbody, MDCDataTableTr, MDCDataTableTd,
        MDCDataTablePagination, MDCButton, MDCSelectOutlined
    )

    @model_template('task-row')
    class TaskRow(MDCDataTableTr):
        def __init__(self, task):
            super().__init__(
                MDCDataTableTd(task.title),
                MDCDataTableTd(task.status),
                MDCDataTableTd(task.owner_name),
            )

    class TaskTable(SubscribeComponentMixin, MDCDataTable):
        publication = 'tasks'          # name of @publish method on your model
        model_template = 'task-row'

        def __init__(self):
            self.page = 0
            self.page_size = 10
            # build static header and pagination controls
            self.header = MDCDataTableThead(
                MDCDataTableTh('Title'),
                MDCDataTableTh('Status'),
                MDCDataTableTh('Owner'),
            )
            self.body = MDCDataTableTbody()  # SubscribeComponentMixin will fill this
            self.pagination = MDCDataTablePagination(
                rows_per_page_select=MDCSelectOutlined(
                    label='Rows per page',
                    optgroups=[(None, [
                        dict(label='10', value='10', selected=True),
                        dict(label='25', value='25'),
                    ], 0)],
                ),
                page_label='',
                next_button=MDCButton('Next', icon='chevron_right', tag='button'),
                prev_button=MDCButton('Prev', icon='chevron_left', tag='button'),
            )
            super().__init__(
                table=MDCDataTableTable(thead=self.header, tbody=self.body),
                pagination=self.pagination,
            )
            # subscription options consumed by get_queryset
            self.subscribe_options = dict(p=self.page, psize=self.page_size)

        def to_html(self, *content, **context):
            # keep subscribe options in sync with UI
            self.subscribe_options['p'] = self.page
            self.subscribe_options['psize'] = self.page_size
            self.reactive_setup(**context)
            return super().to_html(*content, **context)

        def get_content(self):
            # use the registered model_template to render each obj into tbody
            super().get_content()
            # update pagination label from options set in get_queryset
            opts = self.subscription.options
            total = opts.get('total', 0)
            last_page = opts.get('last_page', 0)
            self.pagination.content[-1].content = [  # page label slot
                f'{self.page + 1} of {last_page + 1} ({total} total)'
            ]

        @classmethod
        def get_queryset(cls, user, qs, opts):
            qs = qs.order_by('-created')
            total = qs.count()
            psize = max(1, min(int(opts.get('psize', 10)), 100))
            last_page = max(0, (total - 1) // psize)
            p = max(0, min(int(opts.get('p', 0)), last_page))
            opts.update(dict(psize=psize, p=p, total=total, last_page=last_page))
            start = p * psize
            return qs[start:start + psize]

Wire the next/prev buttons and rows-per-page select with py2js if you want
client-side controls to adjust ``self.page`` / ``self.page_size`` and call
``create_subscription()`` again, or rely on URL query parameters to seed
``subscribe_options`` from the view context. The key point: the pagination
state lives in ``subscribe_options``, and ``get_queryset`` updates ``options``
with totals so you can render page labels. This mirrors the reactive patterns
described in ``ryzom.reactive`` while keeping the MDC structure intact.
