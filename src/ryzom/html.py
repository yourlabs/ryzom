from ryzom.components import Component, CTree, CList, Text


templates = dict()

def template(name, *wrappers):
    global templates
    def decorator(component):
        templates[name] = CTree(*wrappers + (component,))
        return component
    return decorator


class Html(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'html'
        attrs['parent'] = None
        attrs['_id'] = 'html'
        super().__init__(*content, **attrs)


class Head(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'head'
        attrs['parent'] = 'html'
        attrs['_id'] = 'head'
        super().__init__(*content, **attrs)


class Body(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'body'
        attrs['parent'] = 'html'
        attrs['_id'] = 'body'
        super().__init__(*content, **attrs)


class Title(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'title'
        attrs['parent'] = 'head'
        attrs['_id'] = 'title'
        super().__init__(*content, **attrs)


class Meta(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'meta'
        attrs['parent'] = 'head'
        super().__init__(*content, **attrs)


class Link(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'link'
        attrs['parent'] = 'head'
        self.noclose = True
        super().__init__(*content, **attrs)


class Script(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'script'
        attrs['parent'] = 'head'
        attrs.setdefault('type', 'text/javascript')
        super().__init__(*content, **attrs)


class Div(Component):
    '''
    Div component

    Represents a <div> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'div'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class P(Component):
    '''
    Div component

    Represents a <div> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'p'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class A(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'a'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Ul(Component):
    '''
    Ul component

    Represents a <ul> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'ul'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Ol(Component):
    '''
    Ol component

    Represents a <ol> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'ol'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Hr(Component):
    def __init__(self, **attrs):
        attrs['tag'] = 'hr'
        attrs.setdefault('parent', 'body')
        self.noclose = True
        super().__init__(**attrs)


class Br(Component):
    def __init__(self, **attrs):
        attrs['tag'] = 'br'
        attrs.setdefault('parent', 'body')
        self.noclose = True
        super().__init__(**attrs)


class Li(Component):
    '''
    Li component

    Represents a <li> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'li'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Span(Component):
    '''
    Span component

    Represents a <span> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'span'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Textarea(Component):
    '''
    Textarea component

    Represents a <textarea> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'textarea'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Form(Component):
    '''
    Form component

    Represents a <form> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'form'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Input(Component):
    '''
    Input component

    Represents a <input> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        attrs.setdefault('tag', 'input')
        attrs.setdefault('parent', 'body')
        if 'name' in attrs:
            attrs.setdefault('input_id', f'id_{attrs["name"]}')
            attrs.setdefault('label_id', f'id_{attrs["name"]}_label')
        self.noclose = True
        super().__init__(*content, **attrs)


class Select(Component):
    '''
    Select component

    Represents a <select> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'select'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Option(Component):
    '''
    Option component (within Select)

    Represents a <option> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'option'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Optgroup(Component):
    '''
    Option group component (within Select)

    Represents a <optgroup> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'optgroup'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Label(Component):
    '''
    Input component

    Represents a <input> HTML tag

    :parameters: see :class:`Component`
    '''
    tag = 'label'

    def __init__(self, *content, **attrs):
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Button(Component):
    '''
    Button component

    Represents a <button> HTML tag

    :parameters: see :class:`Component`
    '''
    tag = 'button'

    def __init__(self, *content, **attrs):
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Icon(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'i'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Img(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'img'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Nav(Component):
    '''
    Nav component

    Represents a <nav> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'nav'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class H1(Component):
    '''
    H1 component

    Represents a <h1> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'h1'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class H2(Component):
    '''
    H2 component

    Represents a <h2> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'h2'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class H3(Component):
    '''
    H3 component

    Represents a <h3> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'h3'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class H4(Component):
    '''
    H4 component

    Represents a <h4> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'h4'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class H5(Component):
    '''
    H5 component

    Represents a <h5> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'h5'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class H6(Component):
    '''
    H6 component

    Represents a <h6> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'h6'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Caption(Component):
    '''
    Caption component

    Represents a <caption> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'caption'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Table(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'table'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Thead(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'thead'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Tbody(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'tbody'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Tr(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'tr'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Th(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'th'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class Td(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'td'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)


class B(Component):
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'b'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)
