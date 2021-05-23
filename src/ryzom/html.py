from ryzom.components import CList, Component, CTree, HTMLPayload, Markdown, Text
from py2js.transpiler import transpile_body

templates = dict()

def template(name, *wrappers):
    global templates
    def decorator(component):
        if wrappers:
            templates[name] = CTree(*wrappers + (component,))
        else:
            templates[name] = component
        return component
    return decorator


BASIC_TAGS = (
    'a', 'abbr', 'acronym', 'address', 'applet', 'article', 'aside',
    'audio', 'b', 'basefont', 'bdi', 'bdo', 'bgsound', 'big', 'blink',
    'blockquote', 'body', 'button', 'canvas', 'caption', 'center',
    'cite', 'code', 'colgroup', 'content', 'contributors.txt', 'data',
    'datalist', 'dd', 'del', 'details', 'dfn', 'dialog', 'dir', 'div', 'dl',
    'dt', 'em', 'fieldset', 'figcaption', 'figure', 'font', 'footer',
    'frame', 'frameset', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'head',
    'header', 'Heading_Elements', 'hgroup', 'i', 'iframe', 'image',
    'ins', 'isindex', 'kbd', 'keygen', 'label', 'legend', 'li', 'listing',
    'main', 'map', 'mark', 'marquee', 'menu', 'menu#context_menu', 'menuitem',
    'meter', 'multicol', 'nav', 'nextid', 'nobr', 'noembed', 'noframes',
    'noscript', 'object', 'ol', 'optgroup', 'option', 'output', 'p', 'picture',
    'plaintext', 'polygon', 'portal', 'pre', 'progress', 'q', 'rb', 'rp', 'rt',
    'rtc', 'ruby', 's', 'samp', 'section', 'select', 'shadow', 'slot', 'small',
    'spacer', 'span', 'strike', 'strong', 'sub', 'summary', 'sup', 'svg',
    'table', 'tbody', 'td', 'template', 'textarea', 'tfoot', 'th', 'thead',
    'time', 'title', 'tr', 'tt', 'u', 'ul', 'var', 'video', 'xmp',
)

for tag in BASIC_TAGS:
    locals()[tag.capitalize()] = type(tag.capitalize(), (Component,), {'tag': tag})

SELFCLOSE_TAGS = (
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'link', 'meta',
    'param', 'source', 'track', 'wbr',
)

for tag in SELFCLOSE_TAGS:
    locals()[tag.capitalize()] = type(
        tag.capitalize(),
        (Component,),
        {'tag': tag, 'selfclose': True},
    )


class Form(Component):
    tag = 'form'
    attrs = {'enctype': 'multipart/form-data'}


class Script(Component):
    tag = 'script'
    attrs = {'type': 'text/javascript'}


class Style(Component):
    tag = 'style'
    attrs = {'type': 'text/css'}


class Stylesheet(Link):
    attrs = {'type': 'text/css', 'rel': 'stylesheet'}


class Input(Component):
    tag = 'input'

    def __init__(self, *content, **attrs):
        if 'name' in attrs:
            attrs.setdefault('input_id', f'id_{attrs["name"]}')
            attrs.setdefault('label_id', f'id_{attrs["name"]}_label')
        super().__init__(*content, **attrs)


class Icon(Component):
    tag = 'i'


class Head(Component):
    def __init__(self, *content, **attrs):
        super().__init__(*content, **attrs)
        self.content += [
            Meta(
                name='viewport',
                content='width=device-width, initial-scale=1.0',
            ),
            Meta(charset='utf-8'),
        ]


class Html(Component):
    tag = 'html'
    body_class = Body
    head_class = Head

    def __init__(self, *content, **context):
        if 'head' not in context:
            context['head'] = self.head_class(*context.pop('extra_head', []))

        if 'body' not in context:
            context['body'] = self.body_class(*content)

        super().__init__(**context)

        for src in self.stylesheets:
            if not src:
                continue

            if hasattr(src, 'to_html'):
                self.head.content.append(src)
            else:
                self.head.content.append(Stylesheet(href=src))

        for src in self.scripts:
            if not src:
                continue

            if hasattr(src, 'to_html'):
                self.head.content.append(src)
            elif callable(src):
                self.head.content.append(
                    Script(transpile_body(src))
                )
            else:
                self.head.content.append(Script(src=src))

        if title := getattr(self, 'title', None):
            self.__dict__['title'] = Title(title)
            self.head.addchild(self.title)
