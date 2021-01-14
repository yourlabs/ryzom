from ryzom.components import Div, Ul, Li, Span, Input, Button


class Task(Li):
    def __init__(self, task_object):
        attrs = {'class': 'list-group-item'}
        content = [
            Span(task_object.about),
            Button('Done', **{'class': 'btn float-right'}, events={
                'click': f'ryzom.call("remove_task", {{id: {task_object.id}}})'
            })
        ]
        super().__init__(*content, **attrs, _id=f'task_{task_object.id}')


class TaskList(Ul):

    publication = 'all_tasks'

    def __init__(self):
        super().__init__(**{'class': 'list-group'}, _id='tasklist')

    @classmethod
    def subscribe(cls, sub, qs, opts):
        # handle data: filter, order, offset or limit as you wish
        return qs


class TaskForm(Div):
    def __init__(self):
        attrs = {
            'class': 'form-group',
            'style': 'margin:20px',
            'action': '#'
        }
        content = [
            Div(
                Input(**{
                    'id': 'task_input',
                    'type': 'text',
                    'class': 'form-control'
                }),
                Div(
                    Button(
                        'Add',
                        **{
                            'class': 'btn btn-primary'
                        },
                        events={
                            'click': ('ryzom.call("insert_task", '
                                      '{about: $("#task_input").value});'
                                      '$("#task_input").value = ""'
                                      )
                        }
                    ),
                    **{'class': 'input-group-append'}
                ),
                **{'class': 'input-group'}
            )
        ]
        super().__init__(*content, **attrs, _id='task_form')
