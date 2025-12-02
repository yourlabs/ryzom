Material Design form widgets (``ryzom_django_mdc.html``)
========================================================

This module maps Django form widgets to the Material Design components from
``ryzom_mdc.html``. The goal is "drop-in" styling: when your form field renders
with the standard Django template names, the corresponding MDC widget is
picked up automatically and wires labels, helper text, errors, aria attributes,
and IDs for you.

General usage
-------------

- Importing ``ryzom_django_mdc.html`` registers the decorated widget templates
  via ``@widget_template``. Keep your form fields' ``widget.template_name``
  unchanged to benefit from these renderers.
- Each widget exposes ``from_boundfield(cls, bf, **attrs)``. You almost never
  call it directly—Django calls it when rendering the field.
- ``widget_attrs``, ``field_kwargs``, and ``widget_context`` are used internally
  to propagate names, values, required flags, errors, and helper text.

Input widgets
-------------

``MDCInputWidget`` (templates: ``input``, ``date``, ``time``, ``datetime``,
``text``, ``email``, ``password``, ``number``, ``url``)  
    Outlined text field with floating label, helper/error text, and optional
    leading/trailing icons (pass ``licon``/``ticon`` in attrs). Mirrors a
    regular ``<input>`` while adding MDC structure.

``MDCDateInputWidget`` (template: ``date``)  
    Specialization of ``MDCInputWidget`` that forces ``type='date'``. Use for
    date-only fields.

Checkboxes and switches
-----------------------

``MDCCheckboxWidget`` (template: ``checkbox``)  
    Renders a single checkbox with label, helper, and error handling. Uses
    ``MDCCheckboxInput`` under the hood.

``MDCSwitchWidget`` (template: ``switch_option``)  
    Renders a labeled MDC switch. Accepts ``checked`` and standard input attrs,
    and lays out label + switch inline.

Multiple choice checkboxes
--------------------------

``MDCCheckboxSelectMultipleWidget`` (template: ``checkbox_select``)  
    Builds a vertical list of checkbox options. Flattens optgroups into choice
    rows, wraps each with a label, and adds spacing. Uses ``checkbox_option``
    template entries to render each option.

Composite and multi-widget fields
---------------------------------

``MultiWidget`` (templates: ``postgres/widgets/split_array.html``,
``django/forms/widgets/multiwidget.html``)  
    Renders each subwidget in order, using its specific template, and prepends
    field errors. Useful for array or multi-value fields.

``SplitDateTimeWidget`` (template: ``splitdatetime``)  
    Produces a labeled pair of outlined inputs, one for date and one for time,
    preserving icons/labels from subwidgets and aligning them side by side.

Textarea
--------

``TextareaWidget`` (template: ``textarea``)  
    Outlined textarea with floating label, helper and error text, and correct
    aria wiring via ``aria_labelledby``.

File input
----------

``FileInputWidget`` (template: ``file``)  
    Styled file selector using ``MDCFileField``. Shows a “select file” button,
    updates the filename display on change, and places errors beneath. Defaults
    label to “Select file” when not provided.

Select and radio
----------------

``SelectWidget`` (template: ``select``)  
    Outlined select widget using ``MDCSelectOutlined``. Supports optgroups and
    standard choice fields; label is taken from the bound field.

``RadioSelectWidget`` (template: ``radio``)  
    Renders a list of radio inputs using ``MDCRadio`` for each option, along
    with helper/error handling from ``field_kwargs``.

Specialized helpers
-------------------

``MDCCheckbox`` (template: ``checkbox_option``)  
    Checkbox option component used by the multi-select renderer.

``MDCSwitchOption`` (template: ``switch_option``)  
    Input component used inside the switch widget.

``SimpleForm``  
    Convenience wrapper to render any Django form quickly. Arguments:
    ``view`` (to obtain the request/CSRF token) and ``form`` (the bound form).
    Injects a CSRF hidden input and a submit button, whose label defaults to
    ``form.submit_label`` or ``"submit"``.

Choosing the right widget
-------------------------

- Single-line inputs (text/email/number/password/url/date/time/datetime):
  ``MDCInputWidget`` or the date-specific variant.
- Boolean toggle: ``MDCCheckboxWidget`` or ``MDCSwitchWidget`` depending on the
  UX you want.
- Multiple selectable options: ``MDCCheckboxSelectMultipleWidget``.
- Single-choice options: ``SelectWidget`` (dropdown) or ``RadioSelectWidget``
  (list of radios).
- File uploads: ``FileInputWidget``.
- Multi-value or split fields: ``MultiWidget`` / ``SplitDateTimeWidget``.
- Long text: ``TextareaWidget``.

Implementation detail
---------------------

If you provide extra keyword arguments on the form field’s widget (for example
``attrs={'licon': MDCIcon('search')}`` on a text input), they will be passed
through to the ``from_boundfield`` method and rendered appropriately by the
MDC component wrappers.
