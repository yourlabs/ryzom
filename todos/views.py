from ryzom.views import View
from todos.components.base import Document
from todos.components.home import Welcome
from todos.components.tasks import TaskList, TaskForm


class Layout(View):
    def oncreate(self, url):
        self.url = url
        self.content = Document(self)

    def onurl(self, url):
        self.url = url
        if url == 'todos':
            self.reactive('main-container', [TaskList(), TaskForm()])
        else:
            self.reactive('main-container', [Welcome()])
        return True

    def render(self):
        return self.content
