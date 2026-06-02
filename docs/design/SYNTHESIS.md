# Ryzom — Project Synthesis

## What is Ryzom?

Ryzom is a Python component library that replaces Django HTML templates with Python classes. Its tagline: **"Replace HTML Templates with Python Components"**. It draws inspiration from React's component/decorator model while staying server-side Python, and adds optional real-time reactivity via WebSockets.

Status: **Beta**, targeting a production release for an open-source NGO voting platform (built on `microsoft/electionguard-python`).

---

## Package Map

The repository is a mono-repo under `src/`. Each directory is an independently installable package.

| Package | Purpose |
|---|---|
| `ryzom` | Core component engine — renders Python objects to HTML |
| `py2js` | Python → JavaScript transpiler (AST-based) |
| `ryzom_django` | Django integration: template backend, forms, bundle management commands |
| `ryzom_django_channels` | Real-time reactivity layer over Django Channels + Celery |
| `ryzom_django_mdc` | Material Design Components (MDC) bindings for Django forms |
| `ryzom_mdc` | MDC base components (buttons, text fields, icons …) |
| `ryzom_django_autocomplete` | Autocomplete widget integration |
| `ryzom_unpoly` | Thin middleware to set `X-Up-Location` for Unpoly compatibility |

---

## Core Architecture

### 1. Component System (`ryzom/components.py`, `ryzom/html.py`)

Every HTML element is a Python class that extends `Component`.

**Key primitives:**
- `ComponentMetaclass` — processes class-level `attrs`, `style`, `sass`, `scripts`, `stylesheets`, auto-generates `tag` names (kebab-case for custom elements), and wires up JS event handlers.
- `Component` — base class. Holds `content` (children list), `attrs` (a `CAttrs` dict), `id` (UUID), `tag`.
- `CAttrs` / `CStyle` — dict subclasses that translate Python kwarg conventions (`cls` → `class`, `data_foo` → `data-foo`, `addcls`/`rmcls` helpers) and serialize to HTML attribute strings.
- `CList` — tagless container; renders children directly without a wrapping tag.
- `CTree` — chains wrapper components, replaces `{% extends %}`.
- `Text` — raw text node, auto-created for non-component children.
- `Markdown` — renders markdown content; can also walk the parsed HTML tree for `to_obj()` (WebSocket diff mode).

**Rendering pipeline:**
```
Component.render(**context)
  → Component.context()       # bubbles context up from children
  → Component.to_html()       # emits opening tag + content_html + closing tag
      → Component.content_html()  # recurses into children
```

`to_html()` adds `ryzom-id="<uuid>"` to every element automatically, used by the WebSocket diff engine to locate nodes.

`to_obj()` serializes a component tree to a JSON-safe dict — consumed by the WebSocket consumer to push DOM patches.

**Attribute inheritance:**
```python
class Something(Div):
    attrs = dict(cls='something')

class SomethingNew(Something):
    attrs = dict(addcls='new')  # merges — does not override
```

**Style bundling:**
- Class-level `style`/`sass` → extracted into a CSS bundle, component class name injected automatically.
- Instance-level `style` → rendered inline.

**HTML tag generation:**
`ryzom/html.py` dynamically creates one class per tag for both normal (`Div`, `P`, `Span` …) and self-closing (`Img`, `Br`, `Input` …) tags. A few are hand-crafted (`Form`, `Html`, `Head`, `Script`, `Stylesheet`).

The `template(name, *wrappers)` decorator registers a component as the handler for a Django template name:
```python
@template('myapp/mymodel_list.html', BaseTemplate, CardLayout)
class MyList(Ul):
    def __init__(self, **context): ...
```

---

### 2. Python → JavaScript Transpiler (`py2js/`)

An AST-based transpiler that converts a restricted subset of Python to ES6 JavaScript.

**Entry points:**
- `transpile(obj_or_src)` — transpile a function, class, or source string.
- `transpile_body(func)` — transpile a function body only (strips the `def` line).
- `transpile_class(cls, superclass, newname)` — transpile a class, optionally renaming or changing its superclass.

**Supported Python → JS mappings:**
- `self` → `this`, `True/False/None` → `true/false/null`, `print` → `console.log`
- `for x in iterable` → `for (const x of iterable)`
- List comprehensions → generator spread
- f-strings → template literals
- `async def` / `await` → `async`/`await`
- `try/except/finally` with `instanceof` checks
- `lambda` → arrow functions
- Dict/list/tuple literals, slices, attribute access, subscripts

**Limitations (by design):**
- No multiple inheritance, `__mro__`, or most Python stdlib.
- No `*args`, `**kwargs` in class methods.
- `self` must be the first argument in class methods so the transpiler recognises it as a method (not a standalone function).

**Three JS authoring modes inside components:**

1. **HTML way** — define `onclick`, `onsubmit`, etc. as Python methods; they are bundled as `ClassName_onclick(this)` and the attribute is wired up automatically.

2. **WebComponent way** — define an inner `class HTMLElement:` with lifecycle methods (`connectedCallback`, etc.); the transpiler generates an ES6 class that extends `HTMLElement` and calls `window.customElements.define(tag, ClassName)`.

3. **jQuery way** — define a `py2js(self)` method; its body is transpiled and injected as a `<script>` (deprecated, CSP-unsafe).

---

### 3. Django Integration (`ryzom_django/`)

**Template backend** (`template_backend.py`):
- Implements Django's `BaseEngine` interface.
- `get_template(name)` first checks the `html.templates` registry; falls back to importing the name as a dotted Python path.
- Renders by calling `component_instance.render(**context)`.

**Forms** (`forms.py`):
- Monkey-patches `django.forms.BaseForm` and `BoundField` with `.to_component()` and `.to_html()` methods so form objects can be used directly as components.
- Widget-to-component mapping via `@widget_template('widget/template.html')` decorator.

**Bundle management:**
- `ryzom_bundle` management command writes `bundle.js` + `bundle.css` into `ryzom_bundle/static/`.
- `JSBundleView` / `CSSBundleView` serve bundles dynamically in development.
- Bundle generation walks imported modules, finds all components with `HTMLElement` inner classes or event handler methods, and transpiles them.

**CSS bundling** (`ryzom/bundle/css.py`):
- Collects class-level `style` and `sass` declarations from all component classes in the given modules.
- `sass` is passed through `libsass`.

---

### 4. Real-Time Reactivity (`ryzom_django_channels/`)

This layer provides **data binding**: when a model instance changes in the DB, all subscribed clients automatically receive DOM patches over WebSockets.

#### Data flow

```
DB save/delete
  → Django signal (post_save / post_delete)
    → Celery task (async, with retries)
      → ddp_insert_change / ddp_delete
        → diff old vs new queryset
          → send_insert / send_change / send_remove
            → channel layer → Consumer.handle_ddp()
              → WebSocket message to browser
                → ryzom.js patches the DOM
```

#### Key models

| Model | Role |
|---|---|
| `Client` | Represents an open WebSocket connection; stores `channel_name`, `token`, optional `user` FK |
| `Publication` | Named publication tied to a model class and a publish function |
| `Subscription` | Join between `Client` and `Publication`; stores the current queryset as an array of PKs |
| `Registration` | Maps a named registration to a subscriber component and client |

#### Pub/sub API

- `Publishable` mixin — models inherit this to become publishable.
- `@publish` decorator — marks a classmethod as a named publication (returns a queryset).
- `Subscription.get_queryset()` — re-evaluates the publish function, diffs old/new, triggers DDP sends.

#### WebSocket protocol (client ↔ server)

Messages are JSON objects with `{id, type, params}`. Known types:

| Direction | Type | Meaning |
|---|---|---|
| Client → | `subscribe` | Subscribe to a named publication |
| Client → | `unsubscribe` | Cancel a subscription |
| Client → | `method` | Call a server-side method |
| Client → | `geturl` | Navigate to a URL (DDP routing) |
| Client → | `login` / `logout` | Authenticate |
| Client → | `ping` | Keepalive |
| Server → | `Connected` | Welcome; token recognised |
| Server → | `Reload` | Unknown token; browser should reload |
| Server → | `DDP` | DOM patch: `insert`, `change`, or `remove` |
| Server → | `Success` / `Error` | RPC reply |

#### Celery

Signals dispatch DOM-diff work to Celery tasks (`ddp_insert_change_task`, `ddp_delete_task`) with retry logic (5 attempts, 0.2 s sleep between). This avoids blocking the Django request cycle.

---

### 5. Material Design Components (`ryzom_mdc/`, `ryzom_django_mdc/`)

Pre-built component wrappers around [Material Design Components for the Web](https://github.com/material-components/material-components-web):

- `MDCButton`, `MDCButtonRaised`, `MDCButtonOutlined`
- `MDCIcon`, `MDCTextButton`
- Form field renderers that hook into `ryzom_django`'s `@widget_template` system to replace Django's default widget HTML with MDC equivalents.

---

## Thread Safety Note

Component rendering currently **mutates `self`** (e.g., `content` may be modified during `to_html()`). This is acknowledged as a design trade-off. The recommended workaround when sharing component definitions across requests is to wrap instantiation in a lambda:

```python
# Safe:
to_button = lambda: MyButton()

# Unsafe (shared mutable instance):
to_button = MyButton()
```

---

## Dependencies

| Dependency | Used by |
|---|---|
| `django` | `ryzom_django` and all `ryzom_django_*` |
| `channels` + `channels-redis` | `ryzom_django_channels` |
| `daphne` | ASGI server for channels |
| `celery` | Async DDP signal dispatch |
| `lxml` | `Markdown.to_obj()` HTML tree parsing |
| `libsass` | SASS compilation in CSS bundle |
| `markdown` | `Markdown` component |
| `autocomplete-light` | `ryzom_django_autocomplete` |

---

## Developer Workflow

```bash
# Run demo app
pip install -e .[project]
./manage.py migrate
./manage.py runserver
# localhost:8000        → basic form demo
# localhost:8000/reactive → WebSocket reactivity demo

# Tests
py.test

# Build static bundles (production)
./manage.py ryzom_bundle
./manage.py collectstatic
```

---

## Key Design Decisions

1. **Python classes over templates** — embraces the GoF Decorator pattern for GUI composition, the same reason React succeeded; avoids Django's restricted template language.

2. **py2js as a subset bridge** — the goal is not "run Python in the browser" (Transcrypt's goal) but "write browser glue code in Python without context-switching". Only the features needed for DOM event handlers and Web Components are supported.

3. **DDP-inspired protocol** — the WebSocket protocol is loosely modelled after Meteor's DDP (Distributed Data Protocol): publish/subscribe, method calls, and DOM diff messages.

4. **Celery for signal dispatch** — avoids blocking database writes on WebSocket fan-out; the retry wrapper handles transient channel-layer unavailability.

5. **CSS in Python** — class-level `style`/`sass` declarations are extracted at bundle time, keeping style co-located with component logic while producing a single file for production.
