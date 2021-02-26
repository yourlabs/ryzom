from ryzom.views import View

from .components.base import Document
from .components.home import Welcome
from .components.task import TaskList, TaskForm


class Layout(View):
    def oncreate(self, url):
        self.url = url
        self.content = Document(self)

    def onurl(self, url):
        self.url = url.strip('/')
        if self.url == 'todos':
            self.reactive('main-container', [TaskList(), TaskForm()])
        else:
            self.reactive('main-container', [Welcome()])
        return True

    def render(self, request):
        return self.content
