# ryzom_django_mdc

Material Design Components for Django forms.

## Overview

ryzom_django_mdc wraps Material Design Components (MDC) as Ryzom components specifically tailored for Django forms and widgets. It provides styled form inputs, checkboxes, switches, selects, and other form elements with Material Design aesthetics and Django field integration.

## Installation

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'ryzom_django_mdc',
]
```

## Features

- Automatic MDC styling for Django form fields
- Integration with Django's BoundField rendering
- Support for validation states and error display
- Compatible with Django's form rendering system

## Usage

With ryzom_django_mdc installed, Django forms automatically render with Material Design styling when used in Ryzom templates:

```python
from ryzom_django_mdc.html import *

@template('yourapp/form.html', Html)
class FormPage(Div):
    def __init__(self, **context):
        super().__init__(
            context['form'],  # Renders with MDC styling
        )
```

## See Also

- [Main README](../../README.md) for complete documentation
- [ryzom_mdc](../ryzom_mdc/README.md) for base MDC components
- [ryzom_django](../ryzom_django/README.md) for Django integration
