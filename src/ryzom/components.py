'''
Ryzom components declarations.
There's still a lot of tags missing.
They will be added when they'll be needed
'''
import uuid
import importlib


def component_html(path, *args, **kwargs):
    from django.utils.safestring import mark_safe
    try:
        from jinja2.utils import Markup
    except ImportError:
        Markup = None
    import cli2
    ComponentCls = cli2.Node.factory(path).target
    component = ComponentCls(*args, **kwargs)
    html = component.to_html()

    if Markup:
        html = Markup(html)
    return mark_safe(html)


class Component:
    '''Main ryzom component 'abstract' class to be inherited.

    This class defines the common attrsibutes and methods to all
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
    :param dict attrs: HTML attrsibutes (id, class, style, ...)
    :param dict events: The events to add listeners to \
            (click, hover, ...)
    :param str parent: The id of the component that contains the \
            current instance
    :param str _id: The _id of the current instance (must be unique)
    '''

    __publication = None

    def __init__(self, *content, **attrs):
        if 'cls' in attrs:
            attrs['class'] = attrs.pop('cls')  # support HTML class attr

        self.content = list(content) or []

        self._id = attrs.pop('_id', uuid.uuid1().hex)
        self.parent = attrs.pop('parent', None)
        self.tag = attrs.pop('tag', getattr(self, 'tag', 'div'))
        self.selfclose = attrs.pop('selfclose', getattr(self, 'selfclose', False))
        self.noclose = self.tag.lower() in [
            'area', 'base', 'br', 'col', 'embed', 'hr', 'img',
            'input', 'link', 'meta', 'param', 'source', 'track', 'wbr',
        ]

        self.events = attrs.pop('events', {})
        self.attrs = attrs or {}
        self.position = 0

        self.preparecontent()

    def preparecontent(self):
        '''Set the parent and position of children

        meant to be called by __init__().
        This method sets the current component as parent of each child
        Moreover it sets the child's position attribute to its index
        in the current component's content list
        '''
        # handle text node as content
        if self.tag == 'text':
            self.content = self.content[0]
        else:
            for i, c in enumerate(self.content):
                if isinstance(c, str):
                    self.content[i] = c = Text(c)
                c.parent = self._id
                c.position = i

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

    def to_obj(self, context=None):
        '''Get a serializable dict of the instance

        This methods returns a dict representation of the current
        instance. I handles subscriptions that will have this component
        instance _id as parent attribute.
        Recursively sets the content as dict too (maybe recursiveness is not
        a good thing to do without any control of how deep can the tree be,
        there's a risk of stack overflow that we must keep in mind)

        :returns: A serializable representation of the instance
        '''
        sub = None
        if self.publication:
            from ..models import Subscriber, Subscription, Publication
            pub = Publication.objects.get(name=self.publication)
            Subscriber.objects.get_or_create(
                parent_id=self._id,
                parent_module=self.__module__,
                parent_class=self.__class__.__name__
            )
            model_mod = importlib.import_module(pub.model_module)
            model = getattr(model_mod, pub.model_class)
            func = getattr(model, pub.name)
            qs = self.subscribe(None, func(), None)
            self.content = []
            tmpl_module = importlib.import_module(pub.template_module)
            tmpl_class = getattr(tmpl_module, pub.template_class)
            for c in qs:
                self.content.append(tmpl_class(c))

            from django.contrib.postgres.aggregates import ArrayAgg
            sub = Subscription.objects.create(
                parent=self._id,
                publication=pub,
                queryset=qs.aggregate(ids=ArrayAgg('id'))['ids'],
                options=None,
                client=None
            )

        return {
            '_id': self._id,
            'tag': self.tag,
            'content': [
                c if isinstance(c, str) else c.to_obj()
                for c in self.content
            ] if self.tag != 'text' else self.content,
            'parent': self.parent,
            'position': self.position,
            'events': self.events,
            'attrs': self.attrs,
            'publication': self.publication,
            'subscription': f"{sub.id}" if sub else None
        }

    @property
    def publication(self):
        return self.__publication

    @publication.setter
    def publication(self, value=None):
        self.__publication = value

    def to_html(self, **kwargs):
        if self.tag == 'text':
            return f'{self.content}'
        attrs = ''
        for k, v in self.attrs.items():
            if v is True:
                attrs += f'{k.replace("_", "-")} '
            elif v is not False:
                attrs += f'{k.replace("_", "-")}="{v}" '
        attrs += f'ryzom-id="{self._id}"'
        html = ''
        if getattr(self, 'selfclose', False):
            html = f'<{self.tag} {attrs}/>'
        elif getattr(self, 'noclose', False):
            html = f'<{self.tag} {attrs}>'
        else:
            html = f'<{self.tag} {attrs}>'
            if self.publication:
                self.create_subscription(kwargs)
            for c in self.content:
                html += (
                    c.to_html(**kwargs)
                    if getattr(c, 'to_html', None) else str(c)
                )
            html += f'</{self.tag}>'

        js_str = str(self.render_js())
        if js_str:
            js_str = js_str[0:-2]
            js_str += '();'
            #context.scripts += js_str

        return html

    def create_subscription(self, context=None):
        from ..models import Subscriber, Subscription, Publication
        pub = Publication.objects.get(name=self.publication)
        if getattr(self, 'subscription', None):
            return
        else:
            sub = Subscription.objects.filter(
                client=context.request.client,
                publication=pub,
                parent=self._id
            ).first()
            if sub:
                self.subscription = sub
                return
        Subscriber.objects.get_or_create(
            parent_id=self._id,
            parent_module=self.__module__,
            parent_class=self.__class__.__name__
        )
        model_mod = importlib.import_module(pub.model_module)
        model = getattr(model_mod, pub.model_class)
        func = getattr(model, pub.name)
        qs = self.subscribe(None, func(), None)
        self.content = []
        tmpl_module = importlib.import_module(pub.template_module)
        tmpl_class = getattr(tmpl_module, pub.template_class)
        for c in qs:
            self.content.append(tmpl_class(c))

        from django.contrib.postgres.aggregates import ArrayAgg
        self.subscription = Subscription.objects.create(
            parent=self._id,
            publication=pub,
            queryset=qs.aggregate(ids=ArrayAgg('id'))['ids'],
            options=None,
            client=context.request.client
        )

    def render(self, **kwargs):
        return self.to_html(**kwargs)

    def render_js(self):
        return ''


class CTree(Component):
    def __init__(self, *components):
        self.components = components
        self.__name__ = components[-1].__name__

    def __call__(self, **kwargs):
        print(self.components[-1])
        component = self.components[-1](**kwargs)
        for wrapper in reversed(self.components[:-1]):
            component = wrapper(component, **kwargs)
        return component


class CList(Component):
    def to_html(self, **kwargs):
        html_str = ''
        for c in self.content:
            html_str += c.to_html(**kwargs)

        js_str = str(self.render_js())
        if js_str:
            js_str = js_str[0:-2]
            js_str += '();'
            context.scripts += js_str

        return html_str

    def to_obj(self, context=None):
        content = [
            c.to_obj(context)
            for c in self.content
        ]
        return content


class Text(Component):
    '''
    Text component

    Represents a text node

    :parameters: see :class:`Component`
    '''
    def __init__(self, *content, **attrs):
        content = content or []
        attrs = attrs or {}
        attrs['tag'] = 'text'
        attrs.setdefault('parent', 'body')
        super().__init__(*content, **attrs)