from project.component import Div, Ul, Li, Span
from todos.models import Tasks


class Task(Li):
    def __init__(self, task_object):
        content = [Span(task_object.about)]
        super().__init__(content, _id=f'task_{task_object.id}')


class Tasklist(Ul):
    def __init__(self):
        self.subscriptions = [('tasks', ('todos.components.base', 'Task'))]

        content = [
            Task(t)
            for t in Tasks.objects.filter()
        ]
        super().__init__(content, _id='tasklist')


class Base(Div):
    def __init__(self):
        content = [Tasklist()]
        super().__init__(content, _id='tasklist_container')
