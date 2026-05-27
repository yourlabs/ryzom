from django import forms
from django.urls import path
from django.views import generic

from ryzom.components import CList, Markdown, Text
from ryzom.html import H1, H2, H3, A, Br, Code, Div, Hr, Html, Img, Input, Li, P, Pre, Span, Ul
from ryzom_django.bundle import CSSBundle, JSBundle
from ryzom_django.forms import widget_template
from ryzom_django.html import CSRFInput, template

# --- Feature 1: Nested components & children ---

section1 = Div(
    H2("Nesting example"),
    Ul(
        Li(Span("First"), " item"),
        Li(Span("Second"), " item"),
        Li(Span("Third"), " item"),
    ),
    Ul(*[Li(f"Dynamic item {i}") for i in range(1, 4)]),
    Div(Div(P("Deeply nested paragraph"))),
)


# --- Feature 2: HTML attributes ---
#
# Attributes are passed as keyword arguments to the component constructor.
#
# Three translation rules apply:
#
#   1. cls=       → class=
#      'class' is a reserved Python keyword, so Ryzom maps cls → class.
#
#   2. data_foo=  → data-foo=
#      Underscores in attribute names become hyphens, so you can write
#      any data-* or aria-* attribute in plain Python.
#
#   3. addcls=    appends to the existing class without replacing it.
#      rmcls=     removes a specific class from the current class string.
#      These are helpers for modifying class lists without string surgery.
#
# Boolean attributes (e.g. disabled, required) are handled too:
#   disabled=True  → renders as just `disabled` (no value)
#   disabled=False → attribute is omitted entirely
#
# Setting an attribute to None also omits it, useful for conditional attrs.
#
# Attributes live in self.attrs which is a CAttrs instance (a smart dict).
# You can read and write them after construction:
#   component.attrs.cls = 'new-class'
#   component.attrs['data-foo'] = 'bar'

section2 = Div(
    H2("Attributes example"),
    # cls= instead of class= (reserved keyword workaround)
    Div('I have class="box"', cls="box"),
    # data_* → data-* (underscore to hyphen)
    Div('I have data-user-id="42"', data_user_id="42"),
    # aria_* → aria-* (same rule)
    Div('I have aria-label="close"', aria_label="close"),
    # addcls appends without overwriting
    Div('I have class="base extra"', cls="base", addcls="extra"),
    # Boolean attribute: disabled=True → just `disabled` in HTML
    # (using a generic tag component to demonstrate)
    Div(
        A("A normal link", href="#"),
        A("A disabled-looking link", href="#", aria_disabled="true"),
    ),
    # None value → attribute omitted entirely
    Div("No id attr", id=None),
    # Inline style via style= kwarg (instance-level, rendered inline)
    Div("Red text", style="color: red"),
    H3("Modifying attrs after construction"),
    # You can also set attrs after instantiation
    Span("I was unstyled", id="post-construction"),
)

# Modify after construction
post = section2.content[-1]  # the Span we just created
post.attrs["style"] = "color: green; font-weight: bold"
post.attrs.addcls = "modified"


# --- Feature 3: Class-level style → CSS bundle ---
#
# When you define style at the CLASS level, Ryzom does two things:
#
#   1. It does NOT render the style inline on the element.
#      Instead, it extracts it into the CSS bundle (served at /bundles/css).
#
#   2. It automatically adds the class name as a CSS class on the element,
#      so the bundle rule `.ClassName { ... }` targets it correctly.
#
# This is the key difference from instance-level style:
#
#   Instance-level (kwarg):   Div('x', style='color:red')
#     → <div style="color: red">x</div>          (inline, always)
#
#   Class-level (class body): class MyDiv(Div): style = 'color: red'
#     → <div class="MyDiv">x</div>               (class name injected)
#     → CSS bundle gets:  .MyDiv { color: red }  (rule extracted)
#
# Why does this matter?
#   - Inline styles can't use pseudo-selectors (:hover, ::before, etc.)
#   - Class-level styles are deduplicated — 1000 instances share 1 CSS rule
#   - It enables a Content Security Policy (CSP) without unsafe-inline
#
# The style string is standard CSS property syntax with hyphens (not underscores).
# You can also pass a dict: style = {'color': 'red', 'font-size': '1em'}


class AlertBox(Div):
    style = "background: #fff3cd; border: 1px solid #ffc107; padding: 12px; border-radius: 4px"


class SuccessBox(Div):
    style = "background: #d4edda; border: 1px solid #28a745; padding: 12px; border-radius: 4px"


class ErrorBox(Div):
    # style can also be a dict — same result
    style = {
        "background": "#f8d7da",
        "border": "1px solid #dc3545",
        "padding": "12px",
        "border-radius": "4px",
    }


# Subclassing merges the class names — both AlertBox and BigAlertBox
# classes will be on the element, giving you CSS cascade for free.
class BigAlertBox(AlertBox):
    style = "font-size: 1.4em"


section3 = Div(
    H2("Class-level style → CSS bundle"),
    AlertBox("Warning: this style comes from the CSS bundle, not inline."),
    SuccessBox("Success: same here."),
    ErrorBox("Error: style defined as a dict."),
    BigAlertBox("Big alert: subclass merges styles from both classes."),
    P(
        "View the extracted CSS rules at ",
        A("/bundles/bundle.css", href="/bundles/bundle.css"),
        " — search for AlertBox or CardBlock to verify.",
    ),
)


# --- Feature 4: Class-level sass → CSS bundle ---
#
# Just like style=, you can use sass= at the class level.
# The string is passed through libsass before being written to the bundle.
#
# Why use SASS instead of plain CSS?
#   - Nesting: write .Card { h2 { color: red } } instead of two separate rules
#   - Variables: $primary: #007bff; then use $primary everywhere
#   - Mixins, &:hover, &::before — all standard SASS features work
#
# The same two rules from Feature 3 still apply:
#   1. The sass string is extracted into the CSS bundle (not rendered inline).
#   2. The class name is auto-injected as a CSS class on the element.
#
# Two key differences from style=:
#
#   1. sass= uses the INDENTED Sass syntax (no braces, indentation-based),
#      not SCSS. Properties have no semicolons; nesting uses indentation.
#
#   2. The selector is NOT injected automatically — you write the full
#      selector yourself as the first line, then indent the rules under it.
#      This means you control the selector name (use .ClassName to match
#      the auto-injected class, or any other selector you need).
#
# SASS nesting lets you target children without leaving the component:
#   sass = '''
#   .CardBlock
#       color: navy
#       h3
#           color: teal
#   '''
#   → .CardBlock { color: navy; }
#   → .CardBlock h3 { color: teal; }


class CardBlock(Div):
    # Indented Sass syntax: NO braces, indentation defines nesting.
    # The selector is included in the string — Ryzom does NOT wrap it automatically.
    sass = """
    .CardBlock
        background: #e8f4fd
        border-left: 4px solid #0d6efd
        padding: 16px
        margin: 8px 0
        h3
            color: #0d6efd
            margin: 0 0 8px 0
        p
            color: #444
            margin: 0
    """


class HoverCard(Div):
    sass = """
    .HoverCard
        background: white
        border: 1px solid #ccc
        padding: 12px
        cursor: pointer
        transition: box-shadow 0.2s
        &:hover
            box-shadow: 0 4px 12px rgba(0,0,0,0.15)
            border-color: #0d6efd
    """


section4 = Div(
    H2("Class-level sass → CSS bundle"),
    CardBlock(
        H3("SASS nesting"),
        P("This card uses sass= with nested h3 and p rules."),
    ),
    HoverCard("Hover over me — the :hover rule lives in the SASS bundle."),
    P(
        "Like Feature 3, these styles are in the CSS bundle at ",
        A("/bundles/bundle.css", href="/bundles/bundle.css"),
        ", not inline.",
    ),
)


# --- Feature 5: attrs inheritance & merging across subclasses ---
#
# Class-level attrs= is a dict that sets default HTML attributes for every
# instance of that class. Subclasses MERGE their attrs with their parent's —
# they don't replace them.
#
# The merge rules follow the same CAttrs logic as Feature 2:
#   - cls=    sets the class list (replaces parent cls)
#   - addcls= appends to the inherited class list
#   - any other key overwrites the parent's value for that key
#
# Example chain:
#
#   class Base(Div):
#       attrs = dict(cls='base', data_role='widget')
#
#   class Child(Base):
#       attrs = dict(addcls='child')   # keeps 'base', adds 'child'
#
#   class GrandChild(Child):
#       attrs = dict(addcls='grand', data_role='special')  # overrides data-role
#
# Result on GrandChild():
#   <div class="base child grand" data-role="special">
#
# This is how the MDC component library is built: a base component sets
# the MDC class, and subclasses append variant classes via addcls.


class BaseWidget(Div):
    attrs = dict(cls="widget", data_role="widget")


class PrimaryWidget(BaseWidget):
    attrs = dict(addcls="widget--primary")


class LargeWidget(PrimaryWidget):
    attrs = dict(addcls="widget--large", data_size="large")


section5 = Div(
    H2("attrs inheritance & merging"),
    BaseWidget('Base: class="widget", data-role="widget"'),
    PrimaryWidget('Primary: class="widget widget--primary" (addcls merged)'),
    LargeWidget(
        'Large: class="widget widget--primary widget--large", data-size="large"'
    ),
)


# --- Feature 6: Self-closing tags ---
#
# HTML has two kinds of elements:
#   - Normal tags:       <div>content</div>   — need an opening and closing tag
#   - Void (self-closing) tags: <br/>  <img/>  <input/>  — no closing tag, no children
#
# Ryzom generates the right form automatically based on the tag type.
# You never write the closing tag yourself — the class knows whether it needs one.
#
# Self-closing tags in ryzom.html: Img, Br, Hr, Input, Meta, Link, Col, Embed,
#   Param, Source, Track, Wbr, Area, Base, Command, Keygen
#
# They work the same as normal components for attribute passing:
#   Img(src='/logo.png', alt='logo', width='80')
#   Input(type='text', name='q', placeholder='Search…')
#   Br()
#   Hr()
#
# One important constraint: passing children to a self-closing tag is silently
# ignored — void elements cannot have children in HTML.

section6 = Div(
    H2("Self-closing tags"),
    P("An image (Img):"),
    Img(
        src="https://picsum.photos/120/60", alt="placeholder", width="120", height="60"
    ),
    P("A horizontal rule (Hr):"),
    Hr(),
    P("Two line breaks (Br) between these words:", Br(), Br(), "after two breaks"),
    P("A text input (Input):"),
    Input(type="text", placeholder="type here…", name="demo"),
)


# --- Feature 7: CList — tagless container ---
#
# Every component normally wraps its children in a tag: Div → <div>, P → <p>, etc.
# CList is the exception: it has NO tag of its own.
# Its children are rendered directly, one after another, with no wrapping element.
#
# When is this useful?
#
#   1. Returning multiple sibling elements from a component without adding a
#      wrapper div that would break your HTML structure. For example, a component
#      that must render several <li> items — wrapping them in a <div> would be
#      invalid HTML inside a <ul>.
#
#   2. Building helper components that produce a flat list of nodes. Since CList
#      itself has no tag, it is invisible in the rendered HTML.
#
# Compare:
#   Div(A('x'), A('y'))   → <div><a>x</a><a>y</a></div>   (extra wrapper)
#   CList(A('x'), A('y')) → <a>x</a><a>y</a>              (no wrapper)


def nav_links():
    return CList(
        A("Home", href="/"),
        Span(" | "),
        A("Simple", href="/simple/"),
        Span(" | "),
        A("Bundles", href="/bundles/bundle.css"),
    )


section7 = Div(
    H2("CList — tagless container"),
    P(
        "The nav below is rendered by CList — inspect the HTML and you will see"
        " no wrapper element around the links:"
    ),
    nav_links(),
    Hr(),
    P("Compare with Div wrapping the same children:"),
    Div(
        A("Home", href="/"),
        Span(" | "),
        A("Simple", href="/simple/"),
    ),
)


# --- Feature 8: Text & Markdown nodes ---
#
# When you pass a plain Python string as a child of any component, Ryzom
# automatically wraps it in a Text node. Text is a component with tag='text',
# which means it emits its content raw — no wrapping tag at all.
#
#   Div('hello')  →  <div>hello</div>
#              ↑ the string becomes Text('hello') internally
#
# You rarely need to create Text() manually. The main reason to know it exists:
#   - It is the class used for all raw text in the component tree.
#   - If you need to inject pre-escaped HTML, use django's mark_safe() around
#     the string before passing it — Text does NOT escape its content a second
#     time if it's already a SafeString.
#
# Markdown is a subclass of Text that runs the content through the `markdown`
# library before rendering. It accepts:
#   - A multi-line string (textwrap.dedent is applied automatically).
#   - strip_outer_p=True  → removes the wrapping <p>…</p> that markdown adds
#     around a single paragraph, useful when embedding inside another <p>.
#   - Any extra kwargs are forwarded to markdown.markdown() (e.g. extensions=[…]).
#
# Because Markdown produces raw HTML internally, it renders with no extra tag —
# just the HTML that markdown generates, inserted directly in place.

section8 = Div(
    H2("Text & Markdown nodes"),
    H3("Text — implicit"),
    P(
        "Strings passed as children become Text nodes automatically. "
        "This sentence is three Text nodes joined inside a P.",
    ),
    H3("Text — explicit with mark_safe"),
    P(Text("Normal escaped text: <b>not bold</b>")),
    # Using mark_safe bypasses escaping so the tag renders as HTML
    P(
        Text(
            __import__("django.utils.safestring", fromlist=["mark_safe"]).mark_safe(
                "mark_safe text: <b>this IS bold</b>"
            )
        )
    ),
    H3("Markdown"),
    Markdown("""
        ## Markdown heading

        A paragraph with **bold** and *italic* text.

        - item one
        - item two
        - item three
    """),
    H3("Markdown with strip_outer_p"),
    P(
        "Inline markdown: ",
        Markdown("**bold word** inside a paragraph", strip_outer_p=True),
        " — no extra p tag.",
    ),
)


# --- Feature 9: Slots — named keyword children ---
#
# Any component passed as a KEYWORD argument to another component's constructor
# becomes a "slot". Three things happen automatically:
#
#   1. The child gets slot="<name>" added to its attrs.
#   2. The child is stored as self.<name> on the parent, so you can reference it
#      by name inside the parent's __init__ or to_html().
#   3. The child is appended to self.content as usual.
#
# This mirrors the Web Components <slot> concept: named insertion points.
# In the rendered HTML you see slot="header", slot="footer", etc.
#
# Typical use: a card or layout component that needs distinct regions.
# The caller decides WHAT goes in each slot; the component decides WHERE it goes.
#
#   class Card(Div):
#       def __init__(self, *content, header=None, footer=None, **attrs):
#           super().__init__(header, *content, footer, **attrs)
#           # header and footer arrive with slot= already set
#
# The parent can also inspect or modify a slot before rendering:
#   self.header.attrs.addcls = 'card__header'


class Card(Div):
    style = (
        "border: 1px solid #ccc; border-radius: 6px; overflow: hidden; margin: 12px 0"
    )

    def __init__(self, *content, header=None, footer=None, **attrs):
        # Slots arrive as keyword args. We place them explicitly in order:
        # header first, then the body content, then footer.
        # If a slot is None (caller didn't pass it), we skip it.
        parts = []
        if header:
            header.attrs.addcls = "card-header"
            header.attrs["style"] = (
                "background:#f8f9fa; padding:8px 12px; font-weight:bold"
            )
            parts.append(header)
        parts += list(content)
        if footer:
            footer.attrs.addcls = "card-footer"
            footer.attrs["style"] = (
                "background:#f8f9fa; padding:8px 12px; font-size:0.85em; color:#666"
            )
            parts.append(footer)
        super().__init__(*parts, **attrs)


section9 = Div(
    H2("Slots — named keyword children"),
    Card(
        P("This is the card body content."),
        P("It can have multiple children."),
        header=Div("Card Title"),
        footer=Div("Last updated: today"),
    ),
    Card(
        P("A card with no footer slot passed."),
        header=Div("Header only"),
    ),
    Card(
        P("A card with no slots at all — just positional children."),
    ),
)


# --- Feature 10: @template with layout wrappers ---
#
# @template(name) registers a component as the handler for a Django template name.
# When Django renders template_name = 'simple.html', it instantiates SimplePage.
#
# @template(name, *wrappers) does the same thing but wraps the component inside
# one or more layout components — replacing Django's {% extends %}.
#
# How it works:
#   @template('foo.html', Outer, Middle)
#   class Inner(Div): ...
#
#   When 'foo.html' is rendered, Ryzom calls:
#       inner   = Inner(**context)
#       middle  = Middle(inner, **context)
#       outer   = Outer(middle, **context)
#
#   Each wrapper receives the fully instantiated inner component as its first
#   positional child, plus the full view context as kwargs.
#   The outermost wrapper is what actually gets rendered to HTML.
#
# This is the GoF Decorator pattern: wrappers add structure around content
# without the content knowing anything about its surroundings.
#
# The example below defines a two-level layout:
#   PageShell  — the outer HTML document (sets title, a nav bar)
#   ContentBox — a centred content box inside the page
#   Section10Inner — the actual feature content
#
# In a real app you would define PageShell once and reuse it across many views.


class PageShell(Html):
    title = "Layout wrapper demo"
    stylesheets = [CSSBundle()]

    def to_html(self, *content, **context):
        # content = (head, body) — the ContentBox is already inside self.body
        # from Html.__init__. Just prepend the nav bar; do NOT re-add content.
        self.body.content.insert(
            0,
            Div(
                A("← back to simple", href="/simple/"),
                style="padding: 8px; background: #333; color: white",
            ),
        )
        return super().to_html(**context)


class ContentBox(Div):
    style = "max-width: 640px; margin: 32px auto; padding: 0 16px"


@template("section10.html", PageShell, ContentBox)
class Section10Inner(Div):
    def to_html(self, *content, **context):
        return super().to_html(
            H2("Feature 10: @template with layout wrappers"),
            P(
                "This page is rendered by Section10Inner, wrapped inside ContentBox, "
                "wrapped inside PageShell."
            ),
            P("The URL is /simple/layout/ — try it in the browser."),
            P("No {% extends %}, no base.html — just Python classes composing."),
            **context,
        )


class LayoutDemoView(generic.TemplateView):
    template_name = "section10.html"


section10 = Div(
    H2("@template with layout wrappers"),
    P(
        "The @template decorator can accept wrapper classes that act as layout "
        "shells — replacing Django's {% extends %}. "
        "Open ",
        A("/simple/layout/", href="/simple/layout/"),
        " to see a standalone page built from three nested wrapper components.",
    ),
)


# --- Feature 11: context() — bubbling context up from children ---
#
# The rendering pipeline is:
#   render(**context)
#     → self.context(*children, **context)   # walk children, let them enrich context
#     → self.to_html(*children, **context)   # render with the enriched context
#
# Any component can define a context() method. If it does, the parent calls it
# before rendering and MERGES the returned dict into the context passed down
# to all siblings and the parent's own to_html().
#
# This lets a deeply nested child contribute data upward — without the parent
# knowing anything about the child's internals. The classic use case:
# a child component that knows it needs an extra CSS class or script on the
# parent page — it bubbles that requirement up through context().
#
# The walk is depth-first: grandchildren bubble to children, children bubble
# to the root. Each level sees the accumulated result.
#
# Example: a component that signals "I need a <title>" to the parent Html.
#
# Note: context() is called BEFORE to_html(), so by the time the page renders
# the context already has everything the children declared.


class TitleProvider(Div):
    """A component that injects a page_title into context for its ancestors."""

    def __init__(self, title, *content, **attrs):
        self._title = title
        super().__init__(*content, **attrs)

    def context(self, **ctx):
        ctx["page_title"] = self._title
        return ctx


class TitleConsumer(H2):
    """Reads page_title from context — set by a sibling TitleProvider below it."""

    def to_html(self, *content, **context):
        title = context.get("page_title", "(no title bubbled)")
        return super().to_html(f'Title received: "{title}"', **context)


class BubblingDemo(Div):
    def to_html(self, *content, **context):
        # context() was already called recursively over all children before
        # to_html() runs — so page_title is already in context here.
        title = context.get("page_title", "(none)")
        return super().to_html(
            P(f'Parent sees page_title = "{title}"'),
            *self.content,
            **context,
        )


section11 = Div(
    H2("context() — bubbling context up from children"),
    BubblingDemo(
        TitleConsumer(),  # reads page_title from context
        TitleProvider(  # sets page_title in context (defined AFTER consumer
            "Hello from child!",  # but context() walk happens before to_html())
            P("I am the TitleProvider. I set page_title via context()."),
        ),
    ),
    P(
        "Even though TitleConsumer appears before TitleProvider in the tree, "
        "it sees the title — because context() walks all children first, "
        "then to_html() renders them."
    ),
)


# --- Feature 12: Inline event handlers — the HTML way ---
#
# Define onclick, onsubmit, onchange, oninput, or onmouseover as a method
# directly on the component class. Ryzom handles the rest:
#
#   1. ComponentMetaclass detects the method at class-creation time.
#   2. It adds two data attributes to every instance of that class:
#        data-ryzom-component="ClassName"
#        data-ryzom-handlers="onclick"   (comma-separated list)
#   3. The JS bundle transpiles the method as a global function:
#        function ClassName_onclick(self) { ... }   (self → this)
#   4. ryzom.js reads the data attributes on DOMContentLoaded and calls
#        element.addEventListener('click', () => ClassName_onclick(element))
#
# You write the handler body in Python. py2js transpiles it to JavaScript.
# Same translation rules as py2js: self → this, print → console.log, etc.
#
# Supported event methods: onclick, onmouseover, onsubmit, onchange, oninput
#
# The handler receives the event as a parameter (second arg after self).
# IMPORTANT: no *args or **kwargs — py2js only supports simple positional args.


class ClickCounter(Div):
    def __init__(self, *content, **attrs):
        super().__init__(
            "Clicked 0 times",
            style="cursor: pointer; padding: 10px; background: #e9ecef; display: inline-block",
            **attrs,
        )

    def onclick(self, event):
        # dataset values are strings — subtraction coerces to number, addition would concat
        count = (self.dataset.count or 0) - -1
        self.dataset.count = count
        self.innerText = f"Clicked {count} times"


class ColorToggle(Div):
    def __init__(self, *content, **attrs):
        super().__init__(
            "Hover over me",
            style="padding: 10px; background: #d4edda; display: inline-block",
            **attrs,
        )

    def onmouseover(self, event):
        colors = ["#d4edda", "#cce5ff", "#fff3cd", "#f8d7da"]
        idx = ((self.dataset.colorIdx or 0) - -1) % colors.length
        self.dataset.colorIdx = idx
        self.style.backgroundColor = colors[idx]


section12 = Div(
    H2("Inline event handlers — the HTML way"),
    P(
        "This section requires ",
        Code("/static/ryzom.js"),
        " (loaded by SimplePage.scripts). That file contains only the event "
        "delegation glue that reads ",
        Code("data-ryzom-handlers"),
        " attributes and wires them to the transpiled JS functions in bundle.js. "
        "It is NOT the full WebSocket/DDP runtime — that lives in ryzom_django_channels.",
    ),
    P("Click the box to count clicks (handler transpiled from Python onclick method):"),
    ClickCounter(),
    P("Hover to cycle background colours (onmouseover):"),
    ColorToggle(),
    P(
        "Inspect the elements — they have data-ryzom-component and "
        "data-ryzom-handlers attributes. No inline onclick= attribute. "
        "The JS is in ",
        A("/bundles/bundle.js", href="/bundles/bundle.js"),
        " — search for ClickCounter_onclick.",
    ),
)


# --- Feature 13: class HTMLElement — the Web Component way ---
#
# Instead of individual onclick/onmouseover methods, you can define a full
# custom HTML element by nesting a class HTMLElement: inside your component.
#
# py2js transpiles that inner class into a real ES6 Web Component:
#
#   class MyWidget extends HTMLElement {
#       connectedCallback() { ... }   ← called when element is added to the DOM
#       disconnectedCallback() { ... } ← called when element is removed
#       ... any other methods ...
#   }
#   window.customElements.define("my-widget", MyWidget);
#
# The component's tag is automatically set to the kebab-case class name
# (MyWidget → my-widget). This is a real browser custom element — it has its
# own lifecycle, its own JS class, and is registered with customElements.define.
#
# Key differences from the HTML way (Feature 12):
#
#   HTML way:   one method per event, wired via data-ryzom-handlers at runtime
#   WebComponent way: a full JS class, self-contained, browser-native lifecycle
#
# When to use which:
#   - HTML way is simpler for one-off click/change handlers on regular tags
#   - WebComponent way is better for reusable widgets with state, multiple
#     event types, or custom lifecycle logic (init, teardown, timers, etc.)
#
# Inside HTMLElement methods, self → this (the custom element DOM node).
# You can call this.querySelector(), this.dataset, this.style, etc.


class CountdownTimer(Div):
    # tag is auto-set to 'countdown-timer' from the class name
    style = "font-size: 2em; font-weight: bold; font-family: monospace; padding: 12px"

    def __init__(self, seconds=10, **attrs):
        super().__init__(f"{seconds}", data_seconds=seconds, **attrs)

    class HTMLElement:
        def connectedCallback(self):
            window.addEventListener("load", self.start.bind(self))

        def start(self):
            self.remaining = self.dataset.seconds or 10
            self.interval = window.setInterval(self.tick.bind(self), 1000)

        def tick(self):
            self.remaining = self.remaining - 1
            self.innerText = self.remaining
            if self.remaining <= 0:
                window.clearInterval(self.interval)
                self.innerText = "Done!"
                self.style.color = "green"


class ToggleBox(Div):
    style = "border: 2px solid #0d6efd; padding: 12px; cursor: pointer"

    class HTMLElement:
        def connectedCallback(self):
            self.addEventListener("click", self.toggle.bind(self))
            self._open = False

        def toggle(self, event):
            self._open = not self._open
            if self._open:
                self.style.background = "#cce5ff"
                self.innerText = "Clicked! (click again to reset)"
            else:
                self.style.background = "white"
                self.innerText = "Click me to toggle state"


section13 = Div(
    H2("class HTMLElement — Web Component way"),
    P("A countdown timer (connectedCallback starts a setInterval):"),
    CountdownTimer(seconds=120),
    P("A toggle box (connectedCallback wires its own click listener):"),
    ToggleBox("Click me to toggle state"),
    P(
        "These are real custom elements — inspect the DOM and you will see "
        "<countdown-timer> and <toggle-box> tags. "
        "Their JS classes are in ",
        A("/bundles/bundle.js", href="/bundles/bundle.js"),
        ".",
    ),
)


# --- Feature 14: Form rendering ---
#
# Ryzom monkey-patches Django's form and BoundField classes with two methods:
#
#   form.to_component()     → returns a CList of field components
#   form.to_html()          → renders all fields to an HTML string
#   bf.to_component()       → renders a single BoundField to a component
#   bf.to_html()            → renders a single BoundField to an HTML string
#
# A BoundField (bf) is what you get when you iterate a form: `for bf in form`.
# Each bf knows its field type, widget, value, errors, and label.
#
# The rendering is driven by @widget_template (Feature 15), which maps
# widget template names to Ryzom component classes. If no mapping exists,
# the field falls back to Django's default HTML string rendering.
#
# Usage patterns:
#
#   1. Render the whole form at once:
#        Form(CSRFInput(request), form, method='POST')
#      Passing a form object as a child calls form.to_component() automatically.
#
#   2. Render field by field for custom layouts:
#        for bf in form:
#            Div(bf.to_component(), cls='my-field-wrapper')
#
#   3. Render a specific field by name:
#        form['email'].to_component()
#
# The form object is detected as having to_html() and rendered inline.


class SimpleContactForm(forms.Form):
    name = forms.CharField(help_text="Your full name")
    email = forms.EmailField(help_text="We will never share your email")
    message = forms.CharField(widget=forms.Textarea, help_text="Your message")


section14 = Div(
    H2("Form rendering"),
    H3("1. Whole form rendered at once"),
    P("Pass the form as a child — to_component() is called automatically:"),
    Div(
        SimpleContactForm(),
        style="border: 1px solid #ccc; padding: 16px; border-radius: 4px",
    ),
    H3("2. Field by field"),
    P("Iterate the form to render each BoundField individually:"),
    Div(
        *[
            Div(
                bf.to_component(),
                style="border-left: 3px solid #0d6efd; padding: 8px; margin: 4px 0",
            )
            for bf in SimpleContactForm()
        ],
        style="border: 1px solid #ccc; padding: 16px; border-radius: 4px",
    ),
    H3("3. Specific field by name"),
    P('Access a single field via form["fieldname"].to_component():'),
    Div(
        SimpleContactForm()["email"].to_component(),
        style="border: 1px solid #ccc; padding: 16px; border-radius: 4px",
    ),
)


# --- Feature 15: @widget_template — custom widget component ---
#
# @widget_template(template_name) maps a Django widget template name to a
# Ryzom component class. When bf.to_component() is called on a BoundField
# whose widget uses that template, Ryzom calls YourClass.from_boundfield(bf)
# instead of falling back to Django's default HTML rendering.
#
# How the lookup works:
#   bf.to_component()
#     → widget_templates[bf.field.widget.template_name]
#     → YourClass.from_boundfield(bf)
#
# from_boundfield(cls, bf) is a classmethod that receives the BoundField
# and must return a component instance. You have full access to:
#   bf.label        — the field label
#   bf.help_text    — help text
#   bf.errors       — validation errors (a list)
#   bf.value()      — the current value
#   bf.field.widget — the Django widget instance
#   widget_attrs(bf) — dict of HTML attrs from the widget context
#
# You can map multiple widget template names to the same component by
# stacking @widget_template decorators.
#
# Below we define a minimal plain-HTML widget component to show the pattern
# without any MDC dependency:

from ryzom_django.forms import field_kwargs
from ryzom_django.forms import widget_attrs as get_widget_attrs


@widget_template("django/forms/widgets/text.html")
@widget_template("django/forms/widgets/email.html")
class PlainInputWidget(Div):
    style = "margin: 8px 0"

    @classmethod
    def from_boundfield(cls, bf, **attrs):
        wa = get_widget_attrs(bf)
        return cls(
            P(bf.label, style="font-weight: bold; margin: 0 0 4px 0"),
            Input(**wa),
            P(bf.help_text, style="color: #666; font-size: 0.85em; margin: 2px 0")
            if bf.help_text
            else None,
            *[P(e, style="color: red; font-size: 0.85em") for e in bf.errors],
        )


class PlainForm(forms.Form):
    username = forms.CharField(help_text="Letters and numbers only")
    email = forms.EmailField(help_text="Required")


section15 = Div(
    H2("@widget_template — custom widget component"),
    P(
        "The two fields below use PlainInputWidget, registered via "
        "@widget_template. The MDCInputWidget that was registered earlier "
        "for the same template names is now overridden by this one:"
    ),
    Div(
        PlainForm(),
        style="border: 1px solid #ccc; padding: 16px; border-radius: 4px",
    ),
    P(
        "Django widget template names follow the pattern "
        '"django/forms/widgets/<type>.html". '
        "You find them on widget.template_name or in Django source."
    ),
)


# --- Feature 16: scripts & stylesheets on a component ---
#
# Any Html subclass can declare class-level scripts and stylesheets lists.
# Html.__init__ iterates them and injects tags into <head> automatically.
#
# Two value types are supported in each list:
#
#   str   → a URL
#           scripts      = ['/static/app.js']
#             → <script type="text/javascript" src="/static/app.js"></script>
#           stylesheets  = ['/static/app.css']
#             → <link type="text/css" rel="stylesheet" href="/static/app.css"/>
#
#   component instance → embedded as-is (must have to_html())
#           scripts      = [JSBundle()]
#             → JSBundle.to_html() is called, e.g. → <script src="/bundles/bundle.js">
#           stylesheets  = [CSSBundle()]
#             → CSSBundle.to_html() is called, e.g. → <link href="/bundles/bundle.css"/>
#
# Component instances are useful when the href/src must be computed at
# render time (e.g. CSSBundle uses reverse_lazy to resolve the URL).
#
# Inheritance merges the lists — subclasses extend their parent's assets:
#
#   class Base(Html):
#       scripts = ['/static/lib.js']
#
#   class Page(Base):
#       scripts = ['/static/app.js']   # → both lib.js AND app.js in <head>
#
# You've already seen this in action: SimplePage below has both
# stylesheets = [CSSBundle()] and scripts = ['/static/ryzom.js', JSBundle()].
# Open the page source — all three appear in <head>.
#
# A dedicated page that loads the Prism.js syntax highlighter via CDN
# to show scripts/stylesheets with external URLs:

PRISM_CSS = 'https://cdn.jsdelivr.net/npm/prismjs@1/themes/prism.min.css'
PRISM_JS  = 'https://cdn.jsdelivr.net/npm/prismjs@1/prism.min.js'
PRISM_PY  = 'https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-python.min.js'


class PrismPage(Html):
    title = 'Prism syntax highlighting'
    stylesheets = [PRISM_CSS]
    scripts = [PRISM_JS, PRISM_PY]

    def to_html(self, *content, **context):
        self.body.addchild(H1('Feature 16: scripts & stylesheets'))
        self.body.addchild(P(
            'This page loaded Prism.js via the ',
            A('scripts', href='#'),
            ' class attribute. View source to see the three CDN tags in <head>.'
        ))
        self.body.addchild(Div(
            P('The code block below is highlighted by Prism.js:'),
            Pre(Code(
                'class AlertBox(Div):\n'
                '    style = "background: #fff3cd"\n\n'
                'AlertBox("Hello!")',
                cls='language-python',
            )),
        ))
        return super().to_html(**context)


@template('section16.html')
class Section16Page(PrismPage):
    pass


class Section16View(generic.TemplateView):
    template_name = 'section16.html'


section16 = Div(
    H2('scripts & stylesheets on a component'),
    P(
        'Declare scripts = [...] and stylesheets = [...] on any Html subclass. '
        'Strings become URL tags; component instances are rendered as-is. '
        'Subclass lists merge with parent lists automatically.'
    ),
    P(
        'Open ',
        A('/simple/prism/', href='/simple/prism/'),
        ' to see a page that loads Prism.js from CDN via these class attributes.',
    ),
    P('The current page itself uses:'),
    Div(
        P("stylesheets = [CSSBundle()]  → <link href='/bundles/bundle.css'>"),
        P("scripts = ['/static/ryzom.js', JSBundle()]  → two <script> tags"),
        style='background: #f8f9fa; padding: 12px; font-family: monospace; font-size: 0.9em',
    ),
)


# --- Feature 17 & 18: CSS and JS bundles served via BundleView ---
#
# In development (DEBUG=True), Ryzom serves bundles dynamically via two views:
#
#   GET /bundles/bundle.css  → CSSBundleView
#   GET /bundles/bundle.js   → JSBundleView
#
# These are registered in ryzom_django/bundle.py and wired in urls.py:
#
#   if settings.DEBUG:
#       urlpatterns += [path('bundles/', include('ryzom_django.bundle'))]
#
# On every request to /bundles/bundle.css or /bundles/bundle.js, the view:
#   1. Calls get_component_modules() — scans INSTALLED_APPS for
#      app.views, app.urls, app.components, app.html submodules
#   2. Imports each found module to ensure all components are registered
#   3. Iterates every class in those modules
#   4. CSS: collects class-level style= and sass= declarations → one CSS file
#   5. JS:  collects HTMLElement inner classes → ES6 custom elements
#           collects onclick/onchange/etc methods → standalone functions
#
# Why dynamic in dev?
#   No build step needed. Edit a component's style or HTMLElement class,
#   reload the browser — the bundle is regenerated on the next request.
#
# In production you run: ./manage.py ryzom_bundle
# That writes static bundle.js + bundle.css into ryzom_bundle/static/,
# then collectstatic serves them. CSSBundle/JSBundle switch from
# reverse_lazy('bundle_css') to staticfiles_storage.url('bundle.css')
# automatically based on DEBUG.
#
# The auto-discovery scans these submodule names per app:
#   views, urls, components, html
#
# That is why we created components.py — so our simple.py classes are found.
# Any class with:
#   - style= or sass=  → contributes to bundle.css
#   - class HTMLElement:  → contributes a customElements.define() to bundle.js
#   - onclick/onchange/etc → contributes a function to bundle.js

section17 = Div(
    H2('CSS & JS bundles via BundleView (dev)'),
    P(
        'In development, bundles are generated on-the-fly on each request. '
        'No build step. Every reload picks up your latest style and JS changes.'
    ),
    Div(
        P('CSS bundle — all class-level style= and sass= rules:'),
        A('/bundles/bundle.css', href='/bundles/bundle.css'),
        P('JS bundle — all HTMLElement classes and event handler functions:'),
        A('/bundles/bundle.js', href='/bundles/bundle.js'),
        style='background: #f8f9fa; padding: 12px',
    ),
    P('Auto-discovery scans these submodule names per INSTALLED_APP:'),
    Div(
        P('views, urls, components, html'),
        style='background: #f8f9fa; padding: 8px; font-family: monospace',
    ),
    P(
        'In production: ./manage.py ryzom_bundle writes static files. '
        'CSSBundle() and JSBundle() switch URLs automatically via DEBUG.'
    ),
)


@template("simple.html")
class SimplePage(Html):
    stylesheets = [CSSBundle()]
    scripts = ["/static/ryzom.js", JSBundle()]

    def to_html(self, *content, **context):
        self.body.addchild(H1("Ryzom simple example"))
        self.body.addchild(section1)
        self.body.addchild(section2)
        self.body.addchild(section3)
        self.body.addchild(section4)
        self.body.addchild(section5)
        self.body.addchild(section6)
        self.body.addchild(section7)
        self.body.addchild(section8)
        self.body.addchild(section9)
        self.body.addchild(section10)
        self.body.addchild(section11)
        self.body.addchild(section12)
        self.body.addchild(section13)
        self.body.addchild(section14)
        self.body.addchild(section15)
        self.body.addchild(section16)
        self.body.addchild(section17)
        return super().to_html(**context)


class SimpleView(generic.TemplateView):
    template_name = "simple.html"


urlpatterns = [
    path("", SimpleView.as_view()),
    path("layout/", LayoutDemoView.as_view()),
    path("prism/", Section16View.as_view()),
]
