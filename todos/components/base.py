from ryzom.components import Div, Nav, H1
from ryzom.reactive import ReactiveDiv
from todos.components.home import Welcome
from todos.components.tasks import Tasklist, Taskform


class Base(Div):
    def __init__(self, view):
        attr = {
            'class': 'container'
        }
        content = [
            Nav([H1('Todos')], {'class': 'navbar navbar-light bg-light'}),
            ReactiveDiv('main-container', view, [
                Tasklist(),
                Taskform()
            ]) if view.url == 'todos'
            else ReactiveDiv('main-container', view, [Welcome()])
        ]
        super().__init__(content, attr,  _id='tasklist_container')
