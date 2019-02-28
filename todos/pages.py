from .view import View
from .components.base import Base, Tasklist, Taskform, Welcome


class Layout(View):
    def oncreate(self, url):
        self.url = url
        self.content = Base(self)

    def onurl(self, url):
        self.url = url
        if url == 'todos':
            self.setcontent('main-container', [Tasklist(), Taskform()])
        else:
            self.setcontent('main-container', [Welcome()])
        return True

    def render(self):
        return [self.content.to_obj()]
