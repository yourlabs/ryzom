# ryzom

Core component library that replaces HTML templates with Python components.

## Overview

Ryzom provides the foundational framework for building UIs with reusable Python components, following the Decorator pattern inspired by React. Components are Python classes that render HTML tags with support for nested composition, attributes, styles, and JavaScript generation.

## Installation

```bash
pip install ryzom
```

## Quick Start

```python
from ryzom.html import *

# Create components with content
div = Div(cls='container')(
    H1('Hello World'),
    P('Welcome to Ryzom'),
)

# Render to HTML
html = div.render()
```

## Features

- **Component composition**: Nest components using the decorator pattern
- **Attribute handling**: Pythonic API for HTML attributes (`cls`, `data_*`, etc.)
- **Style support**: Define styles as dicts or strings, with SASS support
- **JavaScript generation**: Write JS in Python with py2js transpilation
- **Template registration**: Register components as template replacements

## Component API

### Content

```python
# Pass content as positional arguments
Div('text', P('paragraph'), Span('more'))

# Or use call syntax
Div(cls='foo')('content here')
```

### Attributes

```python
# Attributes use Python naming (underscores become hyphens)
Div(cls='box', data_id='123', aria_label='Info')
# Renders: <div class="box" data-id="123" aria-label="Info">
```

### Inheritance

```python
class Card(Div):
    attrs = dict(cls='card')
    style = dict(padding='1rem', border_radius='4px')

class PrimaryCard(Card):
    attrs = dict(addcls='primary')  # Adds to parent class
```

## See Also

- [Main README](../../README.md) for complete documentation
- [ryzom_django](../ryzom_django/README.md) for Django integration
- [ryzom_mdc](../ryzom_mdc/README.md) for Material Design components
