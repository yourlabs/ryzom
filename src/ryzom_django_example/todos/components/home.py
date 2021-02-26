from django.conf import settings

from ryzom.components import Div, H1, A


class Welcome(Div):
    def __init__(self):
        content = [
            H1('WELCOME !'),
            A('Go to TODO list', **{'href': 'todos'}),
        ]
        super().__init__(*content)
