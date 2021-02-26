from ryzom.components import *
from ryzom.components.django import Static
from ryzom.components.mdc import *
from ryzom.reactive import ReactiveDiv

from .home import Welcome
from .task import TaskList, TaskForm


class Document(Html):
    def __init__(self, view):
        bs_src = 'ryz_ex/css/bootstrap.min.css'
        mdc_js = 'todos/mdc.js'
        mdc_css = 'todos/mdc.css'
        content = [
            Head(
                Title('TODOs'),
                Meta(**{'charset': 'utf-8'}),
                Link(**{
                    'rel': "stylesheet",
                    'href': "https://fonts.googleapis.com/icon?family=Material+Icons",
                }),
                Link(**{'rel': 'stylesheet', 'href': Static(bs_src)}),
                Script(**{
                    'type': 'module',
                    'src': Static(mdc_js)
                }),
                Link(**{
                    'rel': 'stylesheet',
                    'href': Static(mdc_css)
                }),
            ),
            # Body(Base(view))
            Body(
                MdcTopAppBar(
                    'Ryzom Todos',
                    action_items=[
                        ('search', 'Search', 'url', 'events',),
                        ('more_vert', 'Options', None, [
                                ('favorite', 'Favourite', 'url', 'events',),
                                ('favorite', 'Favourite', 'url', 'events',),
                            ],
                        ),
                    ],
                ),
                MdcDrawer(
                    MdcDrawerHeader(
                        drawer_title="Title",
                        drawer_subtitle="subtitle",
                    ),
                    MdcNavList(
                        MdcListItem(
                            Text("Home"),
                            icon='home',
                            href='/',
                            active=True,
                        ),
                        MdcListItem(
                            Text("Todos"),
                            icon='task',
                            href='/todos',
                        ),
                    )
                ),
                MdcAppContent(
                    Base(view),
                ),
            )
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
