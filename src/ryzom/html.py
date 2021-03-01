from ryzom.components import Component, CTree, CList, HTMLPayload, Text


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
    'form', 'frame', 'frameset', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'head',
    'header', 'Heading_Elements', 'hgroup', 'html', 'i', 'iframe', 'image',
    'ins', 'isindex', 'kbd', 'keygen', 'label', 'legend', 'li', 'listing',
    'main', 'map', 'mark', 'marquee', 'menu', 'menu#context_menu', 'menuitem',
    'meter', 'multicol', 'nav', 'nextid', 'nobr', 'noembed', 'noframes',
    'noscript', 'object', 'ol', 'optgroup', 'option', 'output', 'p', 'picture',
    'plaintext', 'portal', 'pre', 'progress', 'q', 'rb', 'rp', 'rt', 'rtc',
    'ruby', 's', 'samp', 'section', 'select', 'shadow', 'slot', 'small',
    'spacer', 'span', 'strike', 'strong', 'style', 'sub', 'summary', 'sup',
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


class Script(Component):
    tag = 'script'
    attrs = {'type': 'text/javascript'}


class Input(Component):
    tag = 'input'

    def __init__(self, *content, **attrs):
        if 'name' in attrs:
            attrs.setdefault('input_id', f'id_{attrs["name"]}')
            attrs.setdefault('label_id', f'id_{attrs["name"]}_label')
        super().__init__(*content, **attrs)


class Icon(Component):
    tag = 'i'
