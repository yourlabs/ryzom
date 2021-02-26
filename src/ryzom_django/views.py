'''
Defines the ryzom View class and the main index view
'''
from django import http
from django.contrib.staticfiles import finders

from ryzom.components import Component, Script
from ryzom.models import Subscription, Publication, Clients

ryzom_js_file = finders.find('ryzom/js/ryzom.js')
ryzom_js_fd = open(ryzom_js_file, 'r')
ryzom_js = f'{ryzom_js_fd.read()}\n'

py2js_js_file = finders.find('ryzom/js/py-builtins.js')
py2js_js_fd = open(py2js_js_file, 'r')
py2js_js = f'{py2js_js_fd.read()}\n'


class View:
    '''
    View class, inherit from this class to create a ryzom View.
    the only parameter it take is the channel name of the client
    creating the view instance.
    It is necessary to overload the methods onurl and render when
    inheriting from this class.
    The methods oncreate() and ondestroy() can also be overloaded
    to run code on those events.

    :param str channel_name: The name of the channel this instance \
            is attached to
    '''
    def __init__(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        self.scripts = ''

    def onurl(self, url):
        '''
        To be overloaded.
        This method will be called whenever a websocket url is required
        (see ryzom.consumers.recv_geturl) and routed to the same view
        controller.
        Its aim is to update the instance inheriting from this class
        on an geturl call.

        :param str url: The url the client is trying to access
        '''
        self.url = url
        return True

    def render(self, request):
        '''
        To be overloaded.
        This method will be called whenever a websocket url is required
        and router to a new View controller.
        Its aim is to render a full content. After that, only reactive
        content should be updated by the onurl() method.

        :param str url: The url the client is trying to access
        '''
        raise NotImplementedError

    def renderHTML(self, url, qs):
        content = self.render(self.request)
        if isinstance(content, Component):
            return http.HttpResponse(
                '<!DOCTYPE html>' +
                content.to_html(self) +
                self.renderJS()
            )

        return content

    def renderJS(self):
        return (
            '<script type="text/javascript">'
            + ryzom_js
            + py2js_js
            + self.scripts
            + '</script>'
        )

    def oncreate(self, url):
        '''
        Hook to optionaly overload.
        This method will be called whenever a new instance of a View is
        created by the consumer.
        Its aim is to setup the view data, such as content, url or whatever.

        :param str url: The url the client is trying to access
        '''
        self.url = url

    def ondestroy(self):
        '''
        Hook to optionaly overload.
        This method will be called whenever a instance of a View is
        destroyed by the consumer.
        '''
        pass

    @classmethod
    def as_view(cls, request, *args, **kwargs):
        view = cls(request, *args, **kwargs)
        view.oncreate(request.path_info)
        view.onurl(request.path_info)

        return view.renderHTML(request.path_info, request.GET.urlencode())


class ReactiveView(View):
    def __init__(self, request):
        self.reactive_components = {}
        super().__init__(request)

    def addReactiveComponent(self, component):
        '''
        Method intended to be used by reactive components.
        Registers a component to the reactive_components dict
        of the view instance.

        :param ReactiveComponent component: The reactive component to \
                attach to this View instance
        '''
        self.reactive_components[component.name] = component

    def reactive(self, name, content):
        '''
        Method to update the content of a reactive component by name.
        the content parameter must be a subclass of ryzom.components.Component

        :param str name: The name of the \
                :class:`ryzom.reactive.ReactiveComponent` to update
        :param Component content: The new content
        '''
        component = self.reactive_components[name]
        component.setcontent(content)

    def renderHTML(self, url, qs):
        def find_tag(c, t):
            if c.tag == t:
                return c
            for children in c.content:
                if c.tag != 'text' and not isinstance(children, str):
                    tag = find_tag(children, t)
                    if tag:
                        return tag

        content = self.render(self.request)

        script = '\n'
        script += f'token = "{self.request.client.token}";\n'
        script += f'current_url = "{url}";\n'
        script += f'query_string = "{qs}";\n'
        script += ryzom_js
        script += self.renderScript(content)

        body = find_tag(content, 'body')
        body.addchild(Script(script))
        return content.to_html(self)

    def renderScript(self, content, set_tag=True):
        script = '(function() {' if set_tag else ''
        content = content if isinstance(content, list) else [content]
        for component in content:
            if isinstance(component, str):
                continue
            if component.publication:
                component.create_subscription(self)
                pub = component.publication
                sub = component.subscription
                script += f'ryzom.subscribe("{pub}", "{sub.id}", "{component._id}",'
                script += 'function(r,e){if (e) {console.log(e);}});\n'
            for event, cb in component.events.items():
                script += f'getElementByUuid("{component._id}").'
                script += f'addEventListener("{event}",' + \
                          f'function(e){{{cb}}});\n'

            if component.tag != 'text':
                script += self.renderScript(component.content, False)
        if set_tag:
            script += '})();'
        return script


def index(request, url=''):
    '''
    Default HTTP django view.
    This view renders the main ryzom template (index.html) to the client.
    index.html contains all the core JS ryzom logic in a basic HTML document.
    it defines the 'url' and 'query_string' variable, templated in the document
    to allow the JS router to know where it is.
    '''
    if request.ryzom.client is None:
        request.ryzom.client = Clients.objects.create()

    view = request.ryzom.view(request.ryzom)
    view.oncreate(url)
    view.onurl(url)

    return view.renderHTML(url, request.GET.urlencode())
