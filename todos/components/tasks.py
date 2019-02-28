from ryzom.components import Div, Ul, Li, Span, Input, Button
from todos.models import Tasks


class Task(Li):
    def __init__(self, task_object):
        attr = {'class': 'list-group-item'}
        content = [
            Span(task_object.about),
            Button('Done', {'class': 'btn float-right'}, {
                'click': f'call("remove_task", {{id: {task_object.id}}})'
            })
        ]
        super().__init__(content, attr, _id=f'task_{task_object.id}')


class Tasklist(Ul):
    def __init__(self):
        # Array of ('ModelName', ('template.module.file', 'TemplateClass'))
        self.subscriptions = [('Tasks', ('todos.components.tasks', 'Task'))]

        content = [
            Task(t)
            for t in Tasks.objects.filter()
        ]
        super().__init__(content, {'class': 'list-group'}, _id='tasklist')


class Taskform(Div):
    def __init__(self):
        attr = {
            'class': 'form-group',
            'style': 'margin:20px',
            'action': '#'
        }
        content = [
            Div(
                attr={'class': 'input-group'},
                content=[
                    Input(attr={
                        'id': 'task_input',
                        'type': 'text',
                        'class': 'form-control'
                    }),
                    Div(
                        attr={'class': 'input-group-append'},
                        content=[
                            Button(
                                content='Add',
                                attr={
                                    'class': 'btn btn-primary'
                                },
                                events={
                                    'click': 'call("insert_task", {   \
                                        about: $("#task_input").value \
                                    }); $("#task_input").value = ""'
                                }
                            )
                        ]
                    )
                ]
            )
        ]
        super().__init__(content, attr, _id='task_form')
