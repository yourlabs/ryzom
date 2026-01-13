# ryzom_unpoly

Unpoly integration for Ryzom.

## Overview

ryzom_unpoly provides lightweight middleware that enables integration with Unpoly, a JavaScript framework for progressive enhancement. It handles Unpoly headers to track page location changes during AJAX requests, facilitating unobtrusive JavaScript enhancement of Ryzom components.

## Installation

Add the middleware to your Django settings:

```python
MIDDLEWARE = [
    ...
    'ryzom_unpoly.middleware.UnpolyMiddleware',
]
```

## Features

- Automatic handling of Unpoly request headers
- Location tracking for AJAX navigation
- Progressive enhancement support for Ryzom components

## Usage

Once the middleware is installed, Unpoly will work seamlessly with your Ryzom components. Add Unpoly attributes to enable progressive enhancement:

```python
from ryzom.html import A

A('Load more', href='/items', **{'up-target': '.item-list'})
```

## See Also

- [Main README](../../README.md) for complete documentation
- [Unpoly documentation](https://unpoly.com/) for Unpoly usage
- [ryzom](../ryzom/README.md) for core components
