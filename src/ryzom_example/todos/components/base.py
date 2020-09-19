from ryzom.components import Html, Head, Body, Meta, Title, Link, Static
from ryzom.components import Div, A, Nav, H1
from ryzom.reactive import ReactiveDiv

from .home import Welcome
from .task import TaskList, TaskForm


class Document(Html):
    def __init__(self, view):
        bs_src = 'ryz_ex/css/bootstrap.min.css'
        content = [
            Head(
                Title('TODOs'),
                Meta(**{'charset': 'utf-8'}),
                Link(**{'rel': 'stylesheet', 'href': Static(bs_src)})
            ),
            Body(Base(view))
        ]
        super().__init__(*content)


class Base(Div):
    def __init__(self, view):
        attrs = {
            'class': 'container',
            '_id': 'tasklist_container',
        }
        content = [
            A(Nav(H1('Todos'),
                  **{'class': 'navbar navbar-light bg-light'}),
              **{'href': '/'}
              ),
            ReactiveDiv('main-container', view, TaskList(), TaskForm()
                        ) if view.url == 'todos'
            else ReactiveDiv('main-container', view, Welcome())
        ]
        super().__init__(*content, **attrs)
