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

## Demo

While Django is not a requirement for Ryzom, we currently only have a demo app
in Django:

```
git clone https://yourlabs.io/oss/ryzom.git
sudo -u postgres createdb -O $UTF -E UTF8 ryzom_django_example
cd ryzom
pip install -e .[project]
./manage.py migrate
./manage.py runserver
# open localhost:8000 for a basic form
# open localhost:8000/reactive for databinding with django channels

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

You may also pass component as keyword arguments, in which case they will be
have a "slot" attribute and be assigned to self:

```py
yourdiv = Div(main=P('content'))
yourdiv.main == P('content', slot='main')
```

#### Special content

Any content that does not define a `to_html` method will be casted to
str and wrapped inside a `Text()` component.

Any content that is `None` will be **removed from** `self.content`.

#### Attributes

HTML tags also have attributes which we have a Pythonic API for:

```py
Div('hi', cls='x', data_y='z').render() == '<div class="x" data-y="z">hi</div>'
```

If you don't like to have the attrs after the content of the element, then keep
in mind you can also pass content components as keyword arguments.

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

Styles may be declared within attrs or on their own too.

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

- Class style attributes will be extracted into a CSS bundle.
- Instance style attributes will be rendered inline.
- Every component that has a style will also render a class attribute.

SASS also works, but won't be interpreted by Ryzom and just be rendered by
libsass as-is:

```py
class FormContainer(Container):
    sass = '''
    .FormContainer
        max-width: 580px
        .mdc-text-field, .mdc-form-field, .mdc-select, form
            width: 100%
    '''
```

### JavaScript

This repository provides a py2js fork that you may use to write JavaScript in
Python. There are three ways you can write js in Python: the "HTML way",
"jQuery way" and the "WebComponent" way.

You must however understand that our purpose is to write JS in Python, rather
than supporting Python in JS like the Transcrypt project. In our case, we will
restrict ourselves to a subset of both the JS and Python language, so things
like Python `__mro__` or even multiple inheritance won't be supported at all.

However, you can still write JS in Python and generate a JS bundle.

#### HTML Way

`onclick`, `onsubmit`, `onchange` and so on may be defined in Python. They will
receive the target element as first argument:

```py
class YourComponent(A):
    def onclick(element):
        alert(self.injected_dependency(element))

    def injected_dependency(element):
        return element.attributes.href.value
```

The above will bundle a `YourComponent_onclick` function, the
`YourComponent_dependency` function, and recursively.

And `YourComponent` will render with `onclick="YourComponent_onclick(this)"`.

#### WebComponent: HTMLElement

The following defines a custom HTMLElement with a JS HTMLElement class, it will
generate a basic web component.

```py
class DeleteButton(Component):
    class HTMLElement:
        def connectedCallback(self):
            this.addEventListener('click', this.delete.bind(this))

        async def delete(self, event):
            csrf = document.querySelector('[name="csrfmiddlewaretoken"]')
            await fetch(this.attributes['delete-url'].value, {
                method: 'delete',
                headers: {'X-CSRFTOKEN': csrf.value},
                redirect: 'manual',
            }).then(lambda response: print(response))
```

This will generate the following JS, which will let the browser responsible for
the components lifecycle, check window.customElement.define documentation for
details.

```js
class DeleteButton extends HTMLElement {
    connectedCallback() {
        this.addEventListener('click',this.delete.bind(this));
    }
    async delete() {
        var csrf = document.querySelector('[name="csrfmiddlewaretoken"]');
        await fetch(this.attributes['delete-url'].value,{
            method: 'delete',
            headers: {'X-CSRFTOKEN': csrf.value},
            redirect: 'manual'
        }).then(
            (response) => {return console.log(response)}
        );
    }
}

window.customElements.define("delete-button", DeleteButton);
```

And that's pretty rock'n'roll if you ask me.

**BUT** there is a catch: currently, you **must** set the first argument to
`self` like in Python, so that the transpiler knows that this function is a
class method and that it shouldn't render with the `function ` prefix that
doesn't work in ES6 classes.

#### The jQuery way

You can do it "the jQuery way" by defining a py2js method in your
component:

```py
class YourComponent(Div):
    def nested_injection():
        alert('submit!')

    def on_form_submit():
        self.nested_injection()

    def py2js(self):
        getElementByUuid(self.id).addEventListener('submit', self.on_form_submit)
```

This will make your component also render the addEventListener statement in a
script tag, and the bundle will package the on_form_submit function.

### Bundles

The component will depend on their CSS and JS bundles. Without Django, you can
do it manually as such:

```py
from ryzom import bundle

your_components_modules = [
    'ryzom_mdc.html',
    'your.html',
]

css_bundle = bundle.css(*your_components_modules)
js_bundle = bundle.js(*your_components_modules)
```

### Django

#### `INSTALLED_APPS`

Add to `settings.INSTALLED_APPS`:

```py
'ryzom',            # add py-builtins.js static file
'ryzom_django',     # enable autodiscover of app_name.html
'ryzom_django_mdc', # enable MDC form rendering
```

#### `TEMPLATES`

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
  ie. `template_name = 'yourapp.html.SomeThing'`

#### Register templates for views

Currently, `ryzom_django` will auto-discover (import) any app's `html.py`
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

#### Bundles

`ryzom_django` app provides 3 commands:

- `ryzom_css`: output the CSS bundle
- `ryzom_js`: output the JS bundle
- `ryzom_bundle`: write `bundle.js` and `bundle.css` in `ryzom_bundle/static`

As well as 2 views, `JSBundleView` and `CSSBundleView` that you can use in
development, include them in your `urls.py` as such:

```py
from django.conf import settings

if settings.DEBUG:
    urlpatterns.append(
        path('bundles/', include('ryzom_django.bundle')),
    )
```

For production, you may write the bundles before running collectstatic as such:

```sh
./manage.py ryzom_bundle
./manage.py collectstatic
```

Then, make sure you use the `Html` component from `ryzom_django` or any
`ryzom_django_*` app, which will include them automatically.

#### Forms

##### API

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

#### Supported API

Low-levels documented in this section are subject to unfriendly change prior to
v1 as we are still researching use cases, please use responsibly.

We are trying to secure the following Component methods that you will like to
override when refactoring code:

- `Component.context(*content, **context)`: alter the context before rendering to bubble
  up new context data from inner components to parent components, aiming to
  solve the same problem we have blocks and extends in jinja templates.
- `Component.content_html(*content, **context)`: render inner HTML
- `Component.to_html(*content, **context)`: renders the outer and inner HTML

#### Not thread safe

Currently, components are not thread safe because much of its rendering code
alters self in a way that will change how it would render again. Some core
component code alters `self.content` during rendering, example in "Special
content": "None" case.

Thread safety is an active discussion topic whenever some thread-unsafe code is
proposed for merge, but we are not yet certain that this is an issue because of
all the better ways Python offers to organize code. For example:

Wrap declarations in lambdas:

```py
class YourView:
    to_button = lambda: YourButton()
```

Instead of:

```py
class YourView:
    to_button = YourButton()
```

We are careful with thread safety in new developments, but it seems must
convenient to just being able to alter `self` on the way.

UNIX was not designed to stop its users from doing stupid things, as that would also stop them from doing clever things.
— Doug Gwyn
