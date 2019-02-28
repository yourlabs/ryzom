import jsonpickle
import uuid


class Component():
    def __init__(self,
                 tag='div',
                 content=None,
                 attr=None,
                 events=None,
                 parent='body',
                 _id=None):
        self._id = _id or uuid.uuid1().hex
        self.parent = parent
        self.tag = 'HTML' if parent is None else tag
        self.attr = {} if attr is None else attr
        self.events = {} if events is None else events
        self.content = [] if content is None else content

        self.preparecontent()

    def preparecontent(self):
        # handle text node as content
        if isinstance(self.content, list):
            for c in self.content:
                c.parent = self._id
        elif isinstance(self.content, str) and self.tag is not 'text':
            self.content = [Text(self.content)]

    def addchild(self, component):
        component.parent = self._id
        self.content.append(component)

    def addchildren(self, components):
        for component in components:
            self.addchild(component)

    def addevents(self, events):
        self.events.update(events)

    def to_json(self):
        return jsonpickle.encode(self)

    def to_obj(self):
        return {
            '_id': self._id,
            'tag': self.tag,
            'content': [
                c.to_obj()
                for c in self.content
            ] if self.tag != 'text' else self.content,
            'parent': self.parent,
            'events': self.events,
            'attr': self.attr,
            'subscriptions': getattr(self, 'subscriptions', [])
        }


class Div(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=uuid.uuid1().hex):
        super().__init__('div', content, attr, events, parent, _id)


class Ul(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=uuid.uuid1().hex):
        super().__init__('ul', content, attr, events, parent, _id)


class Ol(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=uuid.uuid1().hex):
        super().__init__('ol', content, attr, events, parent, _id)


class Li(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=uuid.uuid1().hex):
        super().__init__('li', content, attr, events, parent, _id)


class Span(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=uuid.uuid1().hex):
        super().__init__('span', content, attr, events, parent, _id)


class Text(Component):
    def __init__(self, content=[],
                 parent='body', _id=uuid.uuid1().hex):
        super().__init__('text', content, parent=parent, _id=_id)


class Form(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=uuid.uuid1().hex):
        super().__init__('form', content, attr, events, parent, _id)


class Input(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=uuid.uuid1().hex):
        super().__init__('input', content, attr, events, parent, _id)


class Button(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=uuid.uuid1().hex):
        super().__init__('button', content, attr, events, parent, _id)


class Nav(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=uuid.uuid1().hex):
        super().__init__('nav', content, attr, events, parent, _id)


class H1(Component):
    def __init__(self, content=[], attr={}, events={},
                 parent='body', _id=uuid.uuid1().hex):
        super().__init__('h1', content, attr, events, parent, _id)
