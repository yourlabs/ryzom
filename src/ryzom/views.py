'''
Defines the ryzom View class and the main index view
'''
import os

from django import http
from django.contrib.staticfiles import finders

from ryzom.components import Script


ryzom_js_file = finders.find('ryzom/js/ryzom.js')
ryzom_js_fd = open(ryzom_js_file, 'r')
ryzom_js = f'{ryzom_js_fd.read()}\n'


class View():
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
    def __init__(self, channel_name):
        self.channel_name = channel_name
        self.reactive_components = {}

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
        raise NotImplementedError

    def render(self):
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

        content = self.render()

        def find_tag(c, t):
            if c.tag == t:
                return c
            for children in c.content:
                if c.tag != 'text':
                    tag = find_tag(children, t)
                    if tag:
                        return tag

        script = f'current_url = "{url}";\nquery_string = "{qs}";\n'
        script += ryzom_js
        script += self.renderScript(content)

        body = find_tag(content, 'body')
        body.addchild(Script(script))

        return content.to_html()

    def renderScript(self, content, set_tag=True):
        script = '(function() {' if set_tag else ''
        content = content if isinstance(content, list) else [content]
        for component in content:
            for sub in component.subscriptions:
                script += f'ryzom.subscribe("{sub}","{component._id}",'
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

    def oncreate(self, url):
        '''
        Hook to optionaly overload.
        This method will be called whenever a new instance of a View is
        created by the consumer.
        Its aim is to setup the view data, such as content, url or whatever.

        :param str url: The url the client is trying to access
        '''
        pass

    def ondestroy(self):
        '''
        Hook to optionaly overload.
        This method will be called whenever a instance of a View is
        destroyed by the consumer.
        '''
        pass


def index(request, url=''):
    '''
    Default HTTP django view.
    This view renders the main ryzom template (index.html) to the client.
    index.html contains all the core JS ryzom logic in a basic HTML document.
    it defines the 'url' and 'query_string' variable, templated in the document
    to allow the JS router to know where it is.
    '''
    return http.HttpResponse(
        '<!DOCTYPE html>' +
        request.ryzom.renderHTML(url, request.GET.urlencode())
    )
