'''
Ryzom components declarations.
There's still a lot of tags missing.
They will be added when they'll be needed
'''
import copy
import importlib
import textwrap
import re
import uuid

from py2js.transpiler import transpile_body


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


class HTMLPayload(dict):
    def __init__(self, **kwargs):
        super().__init__(**{
            k.replace('_', '-'): v for k, v in kwargs.items()
        })

    def __getattr__(self, name):
        html_name = name.replace('_', '-')
        if html_name in self:
            return self[html_name]
        raise AttributeError(f'{self} object has no attribute {name}')

    def __setattr__(self, name, value):
        self.__setitem__(name, value)

    def __setitem__(self, name, value):
        name = name.replace('_', '-')
        if value is None:
            if name in self:
                del self[name]
        else:
            super().__setitem__(name, value)

    def update(self, other):
        for key, value in other.items():
            self[key] = value


class CStyle(HTMLPayload):
    @classmethod
    def to_dict(cls, value):
        result = {}
        for rule in value.split(';'):
            if not rule.strip():
                continue
            key, value = rule.split(':')
            result[key.strip()] = value.strip()
        return result


class CAttrs(HTMLPayload):
    def __getitem__(self, name):
        if name == 'style' and 'style' not in self:
            # Create CStyle on the fly
            self['style'] = CStyle()

        if name == 'cls':
            # Translate 'cls' into class
            name = 'class'

        return super().__getitem__(name)

    def __getattr__(self, name):
        if name in self or name in ('style', 'cls'):
            return self.__getitem__(name)
        raise AttributeError(f'{self} object has no attribute {name}')

    def __setitem__(self, name, value):
        if name in ('cls', 'class', 'addcls'):
            if isinstance(value, (list, tuple)):
                value = ' '.join(value)
        if name == 'cls':
            # Maintain the "class" attribute
            name = 'class'
        elif name == 'addcls':
            if 'class' not in self:
                self['class'] = value
            elif self['class']:
                self['class'] += ' ' + value
            else:
                self['class'] = value
            return
        elif name == 'rmcls':
            if 'class' in self:
                self['class'] = self['class'].replace(
                    value, ''
                ).replace('  ', ' ').strip()
            return

        if name == 'style' and isinstance(value, str):
            self.style = CStyle.to_dict(value)
        else:
            super().__setitem__(name, value)

    def update(self, other):
        for key, value in other.items():
            if key == 'style':
                if isinstance(value, str):
                    value = CStyle.to_dict(value)
                self['style'].update(value)
            else:
                self[key] = value

    def to_html(self):
        result = []
        for key, value in self.items():
            if key == 'style':
                new_value = []
                for style_key, style_value in value.items():
                    new_value.append(f'{style_key}: {style_value}')
                value = '; '.join(new_value)

            if value is True:
                result.append(key)
            elif value is not False:
                value = str(value).replace('"', '')
                result.append(f'{key}="{value}"')
        return ' '.join(result)


def noclose(tag):
    return tag.lower() in [
        'area', 'base', 'br', 'col', 'embed', 'hr', 'img',
        'input', 'link', 'meta', 'param', 'source', 'track', 'wbr',
    ]


class ComponentMetaclass(type):
    def __new__(cls, name, bases, class_attrs):
        attrs = CAttrs()
        scripts = list()
        stylesheets = list()

        for base in bases:
            if base_attrs := getattr(base, 'attrs', None):
                attrs.update({k: v for k, v in base_attrs.items() if k != 'style'})
            if extra_scripts := getattr(base, 'scripts', None):
                scripts.extend(extra_scripts)  # scripts are a dict!
            if extra_stylesheets := getattr(base, 'stylesheets', None):
                stylesheets.extend(extra_stylesheets)  # styles are a dict!

        if class_attrs.get('attrs', None):
            attrs.update(class_attrs['attrs'])
        if 'style' in class_attrs:
            attrs.update(dict(style=class_attrs['style']))
        if attrs.get('style', None) or class_attrs.get('sass', None):
            if not attrs.get('class', ''):
                attrs['class'] = name
            else:
                attrs['class'] += f' {name}'
        class_attrs['attrs'] = attrs

        if extra_stylesheets := class_attrs.get('stylesheets', None):
            stylesheets.extend(extra_stylesheets)
        class_attrs['stylesheets'] = stylesheets

        if extra_scripts := class_attrs.get('scripts', None):
            scripts.extend(extra_scripts)
        class_attrs['scripts'] = scripts

        if 'tag' not in class_attrs:
            tag = None
            if 'HTMLElement' not in class_attrs:
                # inherit tag from parent UNLESS I define a WebComponent
                for base in bases:
                    tag = getattr(base, 'tag', None)
                    if tag:
                        break

            if not tag:
                s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
                tag = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()

            class_attrs['tag'] = tag

        if class_attrs.get('tag', None):
            class_attrs['noclose'] = noclose(class_attrs['tag'])

        cls = super().__new__(cls, name, bases, class_attrs)

        from ryzom.bundle.js import AUTOCOMPILE
        for method in AUTOCOMPILE:
            if getattr(cls, method, None):
                class_attrs['attrs'][method] = f'{name}_{method}(this)'

        return cls


class Component(metaclass=ComponentMetaclass):
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
    If no id is specified, a random (but still unique) one will be
    generated.

    :param str tag: The HTML tag of the component
    :param list<Component> content: The component instances contained \
            by the current instance
    :param dict attrs: HTML attrsibutes (id, class, style, ...)
    :param dict events: The events to add listeners to \
            (click, hover, ...)
    :param str parent: The id of the component that contains the \
            current instance
    :param str id: The id of the current instance (must be unique)
    '''

    tag = None  # make sure this class is tagless
    __publication = None

    def __getattribute__(self, name):
        '''Bind style to attrs.style'''
        if name == 'style':
            return self.attrs.style
        return super().__getattribute__(name)

    def __getattr__(self, name):
        '''Instanciate attrs on the fly.'''
        if name == 'attrs':
            self.attrs = CAttrs()
            return self.attrs
        raise AttributeError(f'{self} object has no attribute {name}')

    def __init__(self, *content, **attrs):
        cls = type(self)
        self.content = list(content) or []

        for key in [*attrs.keys()]:
            value = attrs[key]
            if not hasattr(value, 'to_html'):
                continue
            setattr(self, key, value)
            if hasattr(value, 'attrs'):
                value.attrs.setdefault('slot', key)
            self.content.append(attrs.pop(key))

        self.id = attrs.get('id', uuid.uuid1().hex)
        self.parent = attrs.pop('parent', None)

        if 'tag' in attrs:
            self.__dict__['tag'] = attrs.pop('tag')
            self.__dict__['noclose'] = noclose(self.tag)

        self.__dict__['selfclose'] = attrs.pop(
            'selfclose',
            getattr(self, 'selfclose', False),
        )

        self.scripts = copy.deepcopy(getattr(self, 'scripts', []))
        self.stylesheets = copy.deepcopy(getattr(self, 'stylesheets', []))

        self.events = attrs.pop('events', {})

        class_attrs = copy.deepcopy(getattr(self, 'attrs', {}))
        # remove class defined style attribute because it is bundled
        if 'style' in class_attrs:
            class_attrs.pop('style')

        # create an instance attribute from the class attribute
        self.__dict__['attrs'] = class_attrs

        # update with kwargs
        self.attrs.update(attrs)

        self.position = 0

        self.preparecontent()

    def __eq__(self, other):
        if self.attrs != other.attrs or self.tag != other.tag:
            return False
        for my_content, other_content in zip(self.content, other.content):
            if my_content != other_content:
                return False
        return True

    def preparecontent(self):
        '''Set the parent and position of children

        meant to be called by __init__().
        This method sets the current component as parent of each child
        Moreover it sets the child's position attribute to its index
        in the current component's content list
        '''
        for i, c in enumerate(self.content):
            if c is None:
                del self.content[i]
                i -= 1
                continue

            if not hasattr(c, 'to_html'):
                self.content[i] = c = Text(str(c))

            c.parent = self
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
        component.parent = self
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
        instance id as parent attribute.
        Recursively sets the content as dict too (maybe recursiveness is not
        a good thing to do without any control of how deep can the tree be,
        there's a risk of stack overflow that we must keep in mind)

        :returns: A serializable representation of the instance
        '''
        if self.tag == 'text':
            content = self.content
        else:
            content = []
            for c in self.content:
                if not c:
                    continue
                if isinstance(c, (int, float, str)):
                    content.append(c)
                else:
                    content.append(c.to_obj())

        if isinstance(self.parent, str):
            parent_id = self.parent
        else:
            parent_id = self.parent.id

        return {
            'id': self.id,
            'tag': self.tag,
            'content': content,
            'parent': parent_id,
            'position': self.position,
            'script': self.render_js(),
            'attrs': self.attrs
        }

    @property
    def publication(self):
        return self.__publication

    @publication.setter
    def publication(self, value=None):
        self.__publication = value

    def content_html(self, *content, **context):
        html = ''
        for c in content:
            if hasattr(c, 'to_html'):
                newline = '' if getattr(c, 'tag', None) == 'text' else '\n'
                html += newline + c.to_html(**context)
            else:
                html += str(c)

        return html

    def context(self, *content, **context):
        for c in (content or self.content):
            if hasattr(c, 'context'):
                context = c.context(**context)
        return context

    def to_html(self, *content, attrs=None, **context):
        if self.tag == 'text':
            return f'{self.content}'

        attrs = ' '.join([
            (attrs or self.attrs).to_html(),
            f'ryzom-id="{self.id}"'
        ])
        html = ''

        if getattr(self, 'selfclose', False):
            html = f'<{self.tag} {attrs}/>'
        elif getattr(self, 'noclose', False):
            html = f'<{self.tag} {attrs}>'
        else:
            html = f'<{self.tag} {attrs}>'
            content = content or self.content
            html += self.content_html(*content, **context)
            if render_js_str := self.render_js():
                html += '\n'.join([
                    '\n<script type="text/javascript">',
                    render_js_str.strip(),
                    '</script>',
                ])
            if self.content and getattr(self.content[-1], 'tag', None) != 'text':
                newline = '\n'
            else:
                newline = ''
            html += f'{newline}</{self.tag}>'

        return html

    def render(self, *content, **context):
        if 'view' in context:
            self.view = context['view']
        content = content or self.content
        context = self.context(*content, **context)
        return self.to_html(*content, **context)

    def render_js(self):
        if hasattr(self, 'py2js'):
            return transpile_body(self.py2js, self=self)
        return ''

    def render_js_tree(self, lvl=0):
        js_str = str(self.render_js())

        if js_str:
            js_str = js_str

        if hasattr(self, 'content') and isinstance(self.content, (list, tuple)):
            for c in self.content:
                if isinstance(c, Component):
                    js_str += c.render_js_tree(lvl+1)

        return js_str


class CTree(Component):
    def __init__(self, *components):
        self.components = components
        self.__name__ = components[-1].__name__

    def __call__(self, **kwargs):
        component = self.components[-1](**kwargs)
        for wrapper in reversed(self.components[:-1]):
            component = wrapper(component, **kwargs)
        return component


class CList(Component):
    def to_html(self, **kwargs):
        return self.content_html(*self.content, **kwargs)

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
    '''
    tag = 'text'

    def preparecontent(self):
        self.content = self.content[0]


class Markdown(Text):
    def preparecontent(self):
        import markdown
        from django.utils.safestring import mark_safe
        self.content = mark_safe(markdown.markdown(textwrap.dedent(self.content[0])))
