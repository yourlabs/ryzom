'''
Ryzom components declarations.
There's still a lot of tags missing.
They will be added when they'll be required
'''
import jsonpickle
import uuid


class Component():
    '''
    Main ryzom component 'abstract' class to be inherited.
    This class defines the common attributes and methods to all
    components,the main one being to_obj() that format an instance
    as a serializable dict that can be sent to the client over websocket
    the to_html() method is missing for now, it will be usefull when
    implementing Server-Side Rendering

    Upon creation, if not precised, an instance of the Component class
    is considered as a child of the <html> tag, this is not guaranteed
    to be kept in a near future, because it's totally useless.
    Being a childnode of <body> seem a lot more meaningfull.
    If no _id is precised, a random (but still unique) one will be
    generated.
    '''
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
        self.tag = 'HTML' if parent is None else tag
        self.attr = {} if attr is None else attr
        self.events = {} if events is None else events
        self.content = [] if content is None else content

        self.preparecontent()

    def preparecontent(self):
        '''
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
        elif isinstance(self.content, str) and self.tag is not 'text':
            self.content = [Text(self.content)]

    def addchild(self, component):
        '''
        Currently not used at all, but meant to push a new child
        at the end of the content's list
        '''
        component.position = len(self.content)
        component.parent = self._id
        self.content.append(component)

    def addchildren(self, components):
        '''
        Currently not used at all, meant to push children at the
        end of the content's list
        '''
        for component in components:
            self.addchild(component)

    def addevents(self, events):
        '''
        Currently not used, meant to add/update a dict of eventListener
        attached to the DOM element associated with this instance
        '''
        self.events.update(events)

    def to_json(self):
        '''
        No more used, subject to deletion
        '''
        return jsonpickle.encode(self)

    def to_obj(self):
        '''
        This methods returns a dict representation of the current
        instance. I handles subscriptions that will have this component
        instance _id as parent attribute.
        Recursively sets the content as dict too (maybe recursiveness is not
        a good thing to do without any control of how deep can the tree be,
        there's a risk of stack overflow that we must keep in mind)
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
            'subscriptions': getattr(self, 'subscriptions', [])
        }


class Div(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('div', content, attr, events, parent, _id)


class Ul(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('ul', content, attr, events, parent, _id)


class Ol(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('ol', content, attr, events, parent, _id)


class Li(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('li', content, attr, events, parent, _id)


class Span(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('span', content, attr, events, parent, _id)


class Text(Component):
    def __init__(self, content=[],
                 parent='body', _id=None):
        super().__init__('text', content, parent=parent, _id=_id)


class Form(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('form', content, attr, events, parent, _id)


class Input(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('input', content, attr, events, parent, _id)


class Button(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('button', content, attr, events, parent, _id)


class Nav(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('nav', content, attr, events, parent, _id)


class H1(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=None):
        super().__init__('h1', content, attr, events, parent, _id)
