# ryzom_django

Django integration for Ryzom components.

## Overview

ryzom_django bridges Ryzom components with Django by providing a custom template backend, form widget integration, static asset management, and CSRF protection. It enables seamless use of Ryzom components within Django applications.

## Installation

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'ryzom',
    'ryzom_django',
]
```

Add the template backend:

```python
TEMPLATES = [
    {
        'BACKEND': 'ryzom_django.template_backend.Ryzom',
    },
    # ... other backends
]
```

## Features

### Template Registration

Register components as Django template replacements:

```python
from ryzom.html import template, Html, Div

@template('yourapp/yourmodel_list.html', Html)
class YourModelList(Div):
    def __init__(self, **context):
        super().__init__(*[
            P(str(obj)) for obj in context['object_list']
        ])
```

### Form Integration

Django forms automatically work with Ryzom:

```python
# In your component
def __init__(self, **context):
    super().__init__(
        CSRFInput(context['view'].request),
        context['form'],  # BoundFields render as components
        method='post',
    )
```

### Bundle Commands

Generate CSS and JS bundles:

```bash
./manage.py ryzom_css      # Output CSS bundle
./manage.py ryzom_js       # Output JS bundle
./manage.py ryzom_bundle   # Write bundle files to static
```

## See Also

- [Main README](../../README.md) for complete documentation
- [ryzom](../ryzom/README.md) for core components
- [ryzom_django_mdc](../ryzom_django_mdc/README.md) for Material Design form widgets
