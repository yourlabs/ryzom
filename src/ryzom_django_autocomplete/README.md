# ryzom_django_autocomplete

Autocomplete widget integration for Django forms.

## Overview

ryzom_django_autocomplete provides Material Design-based autocomplete input widgets that integrate with Django forms and the django-autocomplete-light library. It offers rich UI components for building autocomplete fields with interactive behavior.

## Features

- Material Design styled autocomplete inputs
- Integration with django-autocomplete-light
- SelectWidget and PlaceholderRemover components
- Support for async data loading

## Usage

```python
from ryzom_django_autocomplete.html import SelectWidget

# Use in your Django form
class MyForm(forms.Form):
    field = forms.CharField(widget=SelectWidget())
```

## See Also

- [Main README](../../README.md) for complete documentation
- [ryzom_django](../ryzom_django/README.md) for Django integration
- [ryzom_mdc](../ryzom_mdc/README.md) for Material Design components
