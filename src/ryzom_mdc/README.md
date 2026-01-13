# ryzom_mdc

Material Design Components for Ryzom.

## Overview

ryzom_mdc provides Material Design Components (MDC) as Python classes, allowing you to build Material Design interfaces without hand-writing MDC HTML. It serves as the foundation for ryzom_django_mdc and provides buttons, inputs, fields, lists, tables, dialogs, and more.

## Installation

Include MDC CSS/JS in your page, then import components:

```python
from ryzom_mdc.html import *
```

## Components

### Buttons

```python
MDCButton('Click me', icon='send')
MDCButtonRaised('Submit')
MDCButtonOutlined('Cancel')
```

### Text Inputs

```python
MDCTextFieldOutlined(
    Input(name='email', type='email'),
    label='Email Address',
    help_text='We will never share your email',
)
```

### Checkboxes and Switches

```python
MDCCheckboxField(
    Input(name='agree', type='checkbox'),
    name='agree',
    label='I agree to the terms',
)

MDCSwitch(checked=True)
```

### Selects

```python
MDCSelectOutlined(
    label='Country',
    optgroups=[
        ('Europe', [
            dict(label='France', value='fr'),
            dict(label='Germany', value='de'),
        ], 0),
    ],
    name='country',
)
```

### Data Tables

```python
MDCDataTable(
    table=MDCDataTableTable(
        thead=MDCDataTableThead(
            MDCDataTableTh('Name'),
            MDCDataTableTh('Status'),
        ),
        tbody=MDCDataTableTbody(
            MDCDataTableTr(
                MDCDataTableTd('Item 1'),
                MDCDataTableTd('Active'),
            ),
        ),
    ),
)
```

### Dialogs

```python
MDCDialog(
    MDCDialogTitle('Confirm'),
    MDCDialogContent(P('Are you sure?')),
    actions=MDCDialogActions(
        MDCDialogCloseButtonOutlined('Cancel'),
        MDCDialogAcceptButton('Confirm'),
    ),
)
```

### Feedback

```python
MDCSnackBar('Operation successful', status='success')
MDCErrorList('Field is required', 'Invalid format')
```

## See Also

- [Main README](../../README.md) for complete documentation
- [MDC documentation](../../docs/source/ryzom_mdc.rst) for full component reference
- [ryzom_django_mdc](../ryzom_django_mdc/README.md) for Django form integration
