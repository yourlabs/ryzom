'''
Ryzom components declarations.
There's still a lot of tags missing.
They will be added when they'll be needed
'''
import cli2
import jsonpickle
import uuid


def component_html(path, *args, **kwargs):
    from django.utils.safestring import mark_safe
    try:
        from jinja2.utils import Markup
    except ImportError:
        Markup = None
    Component = cli2.Importable.factory(path).target
    component = Component(*args, **kwargs)
    html = component.to_html()

    # DEBUG:
    print()
    print()
    print()
    print('HTML')
    print(html)
    print()
    print()

    if Markup:
        html = Markup(html)
    return mark_safe(html)


class Component:
    '''Main ryzom component 'abstract' class to be inherited.

    This class defines the common attributes and methods to all
    components,the main one being to_obj() that format an instance
    as a serializable dict that can be sent to the client over websocket
    the to_html() method is missing for now, it will be useful when
    implementing Server-Side Rendering

    Upon creation, if not specified, an instance of the Component class
    is considered as a child of the <html> tag, this is not guaranteed
    to be kept in a near future, because it's totally useless.
    Being a childnode of <body> seem a lot more meaningful.
    If no _id is specified, a random (but still unique) one will be
    generated.

    :param str tag: The HTML tag of the component
    :param list<Component> content: The component instances contained \
            by the current instance
    :param dict attr: HTML attributes (id, class, style, ...)
    :param dict events: The events to add listeners to \
            (click, hover, ...)
    :param str parent: The id of the component that contains the \
            current instance
    :param str _id: The _id of the current instance (must be unique)
    '''

    __subscriptions = []

    def __init__(self,
                 tag='div',
                 content=None,
                 attr=None,
                 events=None,
                 parent='body',
                 _id=None):
        self._id = _id or uuid.uuid1().hex
        self.parent = parent
        self.position = 0
        self.tag = tag
        self.attr = {} if attr is None else attr
        self.events = {} if events is None else events
        self.content = [] if content is None else content

        self.preparecontent()

    def preparecontent(self):
        '''Set the parent and position of children

        meant to be called by __init__().
        This method sets the current component as parent of each child
        Moreover it sets the child's position attribute to its index
        in the current component's content list
        '''
        # handle text node as content
        if isinstance(self.content, list):
            for i, c in enumerate(self.content):
                c.parent = self._id
                c.position = i
                if isinstance(c, str):
                    self.content[i] = Text(c)
        elif isinstance(self.content, str) and self.tag is not 'text':
            if self.content:
                self.content = [Text(self.content)]
            else:
                self.content = []

    def addchild(self, component):
        '''Add a child component

        Currently not used at all, but meant to push a new child
        at the end of the content's list
        A call to preparecontent() should follow the call to this method

        :param Component component: The child component to add to the \
                content of the current instance
        '''
        component.position = len(self.content)
        component.parent = self._id
        self.content.append(component)

    def addchildren(self, components):
        '''Add a list of children

        Currently not used at all, meant to push children at the
        end of the content's list.
        A call to preparecontent() should follow the call to this method

        :param list(Component) components: The component list to insert \
                in the content of the current instance
        '''
        for component in components:
            self.addchild(component)

    def addevents(self, events):
        '''Add events to instance

        Currently not used, meant to add/update a dict of eventListener
        attached to the DOM element associated with this instance

        :param dict events: The dict to update events with
        '''
        self.events.update(events)

    def to_json(self):
        '''
        No more used, subject to deletion

        :returns: A serialized JSON representation of the instance
        '''
        return jsonpickle.encode(self)

    def to_obj(self):
        '''Get a serializable dict of the instance

        This methods returns a dict representation of the current
        instance. I handles subscriptions that will have this component
        instance _id as parent attribute.
        Recursively sets the content as dict too (maybe recursiveness is not
        a good thing to do without any control of how deep can the tree be,
        there's a risk of stack overflow that we must keep in mind)

        :returns: A serializable representation of the instance
        '''
        return {
            '_id': self._id,
            'tag': self.tag,
            'content': [
                c.to_obj()
                for c in self.content
            ] if self.tag != 'text' else self.content,
            'parent': self.parent,
            'position': self.position,
            'events': self.events,
            'attr': self.attr,
            'subscriptions': self.subscriptions
        }

    @property
    def subscriptions(self):
        return self.__subscriptions

    @subscriptions.setter
    def subscriptions(self, value=[]):
        self.__subscriptions = value

    def to_html(self):
        if self.tag == 'text':
            return f'{self.content}'
        attr = ''
        for k, v in self.attr.items():
            if v is True:
                attr += f'{k} '
            elif v is not False:
                attr += f'{k}="{v}" '
        attr += f'ryzom-id="{self._id}"'
        html = ''
        if getattr(self, 'selfclose', False):
            html = f'<{self.tag} {attr}/>'
        elif getattr(self, 'noclose', False):
            html = f'<{self.tag} {attr}>'
        else:
            html = f'<{self.tag} {attr}>'
            for c in self.content:
                html += c.to_html() if getattr(c, 'to_html', None) else str(c)
            html += f'</{self.tag}>'
        return html


class Html(Component):
    def __init__(self, content=[]):
        super().__init__('html', content, parent=None, _id='html')


class Head(Component):
    def __init__(self, content=[]):
        super().__init__('head', content, parent='html', _id='head')


class Body(Component):
    def __init__(self, content=[]):
        super().__init__('body', content, parent='html', _id='body')


class Title(Component):
    def __init__(self, content=''):
        super().__init__('title', content, parent='head', _id='title')


class Meta(Component):
    def __init__(self, attr={}):
        super().__init__('meta', attr=attr, parent='head')


class Link(Component):
    def __init__(self, attr={}):
        self.noclose = True
        super().__init__('link', attr=attr, parent='head')


class Script(Component):
    def __init__(self, content='', attr={}):
        super().__init__('script', content, attr, parent='head')


class Div(Component):
    '''
    Div component

    Represents a <div> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('div', content, attr, events, parent, _id)


class A(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('a', content, attr, events, parent, _id)


class Ul(Component):
    '''
    Ul component

    Represents a <ul> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('ul', content, attr, events, parent, _id)


class Ol(Component):
    '''
    Ol component

    Represents a <ol> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('ol', content, attr, events, parent, _id)


class Li(Component):
    '''
    Li component

    Represents a <li> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('li', content, attr, events, parent, _id)


class Span(Component):
    '''
    Span component

    Represents a <span> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('span', content, attr, events, parent, _id)


class Text(Component):
    '''
    Text component

    Represents a text node

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=[],
                 parent='body', _id=None):
        super().__init__('text', content, parent=parent, _id=_id)


class Textarea(Component):
    '''
    Textarea component

    Represents a <textarea> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('textarea', content, attr, events, parent, _id)


class Form(Component):
    '''
    Form component

    Represents a <form> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('form', content, attr, events, parent, _id)


class Input(Component):
    '''
    Input component

    Represents a <input> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('input', content, attr, events, parent, _id)


class Select(Component):
    '''
    Select component

    Represents a <select> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('select', content, attr, events, parent, _id)


class Option(Component):
    '''
    Option component (within Select)

    Represents a <option> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('option', content, attr, events, parent, _id)


class Optgroup(Component):
    '''
    Option group component (within Select)

    Represents a <optgroup> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('optgroup', content, attr, events, parent, _id)


class Label(Component):
    '''
    Input component

    Represents a <input> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('label', content, attr, events, parent, _id)


class Button(Component):
    '''
    Button component

    Represents a <button> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('button', content, attr, events, parent, _id)


class Nav(Component):
    '''
    Nav component

    Represents a <nav> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('nav', content, attr, events, parent, _id)


class H1(Component):
    '''
    H1 component

    Represents a <h1> HTML tag

    :parameters: see :class:`Component`
    '''
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('h1', content, attr, events, parent, _id)
