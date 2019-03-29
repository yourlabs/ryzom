from ryzom.components import Html, Head, Body, Meta, Title, Link
from ryzom.components import Div, A, Nav, H1
from ryzom.reactive import ReactiveDiv
from todos.components.home import Welcome
from todos.components.tasks import Tasklist, Taskform


class Document(Html):
    def __init__(self, view):
        bs_src = '/static/css/bootstrap.min.css'
        content = [
            Head([
                Title('TODOs'),
                Meta(attr={'charset': 'utf-8'}),
                Link(attr={'rel': 'stylesheet', 'href': bs_src})
            ]),
            Body([Base(view)])
        ]
        super().__init__(content)


class Base(Div):
    def __init__(self, view):
        attr = {
            'class': 'container'
        }
        content = [
            A([Nav([H1('Todos')], {'class': 'navbar navbar-light bg-light'})], {
                'href': '/'
            }),
            ReactiveDiv('main-container', view, [
                Tasklist(),
                Taskform()
            ]) if view.url == 'todos'
            else ReactiveDiv('main-container', view, [Welcome()])
        ]
        super().__init__(content, attr,  _id='tasklist_container')
