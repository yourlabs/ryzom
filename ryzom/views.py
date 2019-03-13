'''
Defines the ryzom View class and the main index view
'''
from django.shortcuts import render


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
    return render(request, 'index.html', {
            'url': url,
            'query_string': request.GET.urlencode()
        })
