# flake8: noqa: F401

from .components import (
    component_html,
    Component,
    Html,
    Head,
    Body,
    Title,
    Meta,
    Link,
    Script,
    Div,
    A,
    Ul,
    Ol,
    Li,
    Span,
    Text,
    Textarea,
    Form,
    Input,
    Select,
    Option,
    Optgroup,
    Label,
    Button,
    Icon,
    Nav,
    H1,
    H2,
    H3
)

import os

if 'DJANGO_SETTINGS_MODULE' in os.environ:
    from .contrib.django import Static
