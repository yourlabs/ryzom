from ryzom.components import Div, Button, H1


class Welcome(Div):
    def __init__(self):
        content = [
            H1('WELCOME !'),
            Button('todos', events={
                'click': 'route("todos")'
            })]
        super().__init__(content)
