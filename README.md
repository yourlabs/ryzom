# Ryzom: Replace HTML Templates with Python Components

## Why?

Because while frameworks like Django claim that "templates include a restricted
language to avoid for the HTML coder to shoot themself in the foot", the GoF on
the other hand states that Decorator is the pattern that is most efficient for
designing GUIs, which is actually a big part of the success encountered by
frameworks such as React.

## What?

Ryzom basically offers Python Components, with extra sauce of bleeding edge
features such as "compiling Python code to JS", and "data binding" (DOM
refreshes itself when data changes in the DB) if you enable websockets.

## State

Currently in Beta stage, we are brushing up for a production release in an Open
Source project for an NGO defending democracy, with an online voting platform
secured with homomorphic encryption, basically a Django project built on top of
microsoft/electionguard-python.

It's **not** ready for general use, but should hopefully be pretty soon...
after all, this project has been under R&D sponsored by YourLabs for years now
and it's about time!

## Demo

```
git clone https://yourlabs.io/oss/ryzom.git
sudo -u postgres createdb -O $UTF -E UTF8 ryzom_django_example
cd ryzom
pip install -e .
./manage.py migrate
./manage.py runserver

# to run tests:
py.test
```

## Usage

### HTML

#### Content

Components are Python classes in charge of rendering an HTML tag. As such, they
may have content (children):

```py
from ryzom.html import *

yourdiv = Div('some', P('content'))
yourdiv.render() == '<div>some <p>content</p></div>'
```

Most components should instanciate with `*content` as first argument, and you
can pass as many children as needed there. These goes into `self.content` which
you can also change after instanciation.

#### Attributes

HTML tags also have attributes which we have a Pythonic API for:

```py
Div('hi', cls='x', data_y='z').render() == '<div class="x" data-y="z">hi</div>'
```

Declarative and inheritance are supported too:

```py
class Something(Div):
    attrs = dict(cls='something', data_something='foo')


class SomethingNew(Something):
    attrs = dict(addcls='new')  # how to add a class without re-defining


yourdiv = SomethingNew('hi')
yourdiv.render() == '<div class="something new" data-something="foo">hi</div>'
```

#### Styles

Style attributes will also merge, they may be declared within attrs or on their
own too.

```py
class Foo(Div):
    style = dict(margin_top='1px')

# is the same as:

class Foo(Div):
    style = 'margin-top: 1px'

# is the same as:

class Foo(Div):
    attrs = dict(style='margin-top: 1px')
```

They are inheritable like attributes.

### Django

##### `INSTALLED_APPS`

Add to `settings.INSTALLED_APPS`:

```py
'ryzom',            # add py-builtins.js static file
'ryzom_django',     # enable autodiscover of app_name.components
'ryzom_django_mdc', # enable MDC form rendering
```

##### `TEMPLATES`

While ryzom offers to register components to template names, `ryzom_django`
offers the template backend to make any use of that with Django, add the
template backend as such in `settings.py`:

```py
TEMPLATES = [
    {
        'BACKEND': 'ryzom_django.template_backend.Ryzom',
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

This template backend will allow two usages:

- overriding html template names with components,
- using components import path in dotted-style for `template_name`,
  ie. `template_name = 'yourapp.components.SomeThing'`

##### Register templates for views

Currently, `ryzom_django` will auto-discover (import) any app's `components.py`
file. As such, this is where you can define all your view templates
replacements with `ryzom.html.template`. For example, to set the default
template for a `django.views.generic.ListView` with model `YourModel`:

```py
from ryzom_mdc import *

class BaseTemplate(Html):
    title = 'Your site title'


@template('yourapp/yourmodel_list.html', BaseTemplate)
class YourModelList(Ul)
    def __init__(self, **context):
        super().__init(*[Li(f'{obj}') for obj in context['object_list'])])
```

Import the `html` module from ryzom_mdc or from ryzom, depending on the flavor
you want. You can nest components on the fly as you register a template, which
replaces `{% extends %}`.

You may chain as many parents as you would like, for example you could have a
"card" layout that sets a small content width:

```py
class CardLayout(Div):
    style='max-width: 20em; margin: auto'

@html.template('yourapp/yourmodel_form.html', BaseTemplate, CardLayout)
class YourModelForm(Form):
    def __init__(self, **context):
        super().__init__(
            CSRFInput(context['view'].request),
            context['form'],
            method="post",
        )

```

##### Forms

###### API

ryzom_django.forms patches django.forms.BaseForm with 2 new methods:

- `BaseForm.to_html()`: render the HTML, makes the BaseForm objects "quack"
  like a component, also useable in non-ryzom templates to get the rendering
  with `{{ form.to_html }}`

- `BaseForm.to_component()`: called by to_html(), this is where the default
  layout is generated, which you can override to customize the form object
  rendering. It will return a CList (tagless component list) of the
  to_component() result of every boundfield.

ryzom_django.forms patches django.forms.BoundField with 2 new methods:

- `BoundField.to_component()`: this will return the Component template
  registered for the field widget template name if any, in which case it will
  use the `from_boundfield(boundfield)` of that template.

- `BoundField.to_html()`: render the HTML, makes the BoundField objects "quack"
  like components.

As such, you can configure how a form object renders by overriding the
`to_component()` method, and use BoundField objects like components too:

```py
def to_component(self):
    return Div(
        H3('Example form!'),
        self['some_field'],  # BoundField quacks like a Component!
        Div(
            Input(type='submit'),
        )
    )
```

#### Demo

An example Django project is available in `src/ryzom_django_example/`, example
code is in the `urls.py` file.
