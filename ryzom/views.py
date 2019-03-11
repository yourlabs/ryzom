import json
from django.shortcuts import render
from ryzom.models import Clients


class View():
    def __init__(self, channel_name):
        self.channel_name = channel_name
        self.reactive_components = {}

    def addReactiveComponent(self, component):
        self.reactive_components[component.name] = component

    def reactive(self, name, content):
        component = self.reactive_components[name]
        component.setcontent(content)

    def onurl(self, url):
        raise NotImplementedError

    def render(self, url):
        raise NotImplementedError

    def oncreate(self, url):
        pass

    def ondestroy(self, url):
        pass


def index(request, url=''):
    return render(request, 'index.html', {
            'url': url,
            'query_string': request.GET.urlencode()
        })
