# py2js

Python to JavaScript transpiler for Ryzom components.

## Overview

py2js provides a transpiler that converts Python code to JavaScript, enabling shared logic that runs on both server and client. It parses Python AST, transpiles functions and classes, and formats the resulting JavaScript code.

## Usage

py2js is used internally by Ryzom to transpile component methods like `onclick`, `onsubmit`, and `HTMLElement` class definitions into JavaScript that runs in the browser.

```python
from ryzom.html import Div

class YourComponent(Div):
    def onclick(element):
        alert('Clicked!')
```

The above will generate JavaScript and render the component with `onclick="YourComponent_onclick(this)"`.

## Features

- Transpiles Python functions to JavaScript functions
- Supports ES6 class generation for web components
- Handles async/await syntax
- Recursive dependency resolution for nested function calls

## See Also

- [Main README](../../README.md) for complete documentation
- [ryzom](../ryzom/README.md) for core component usage
