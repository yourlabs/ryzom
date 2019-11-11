"""
Render Django forms using ryzom components.
"""
from .components import *


class NFErrors(Div):
    def __init__(self, form):
        content = []
        for error in form.non_field_errors():
            content.append(
                # Render non-field error.
                Span([Text(error)],
                     {"class": "small error"}
                     )
                )
        return super().__init__(
            content,
        )


class HiddenFields(Div):
    def __init__(self, form):
        content = []
        for hidden in form.hidden_fields():
            content.append(
                # Render hidden field.
                [Div(
                    [Input([],
                           {"type": "hidden",
                            }
                           )
                     ]
                    )
                    ]
                )
        return super().__init__(
            content,
        )


class Fields(Div):
    def __init__(self, form):
        content = []
        for field_name, field in form.fields.items():
            content.append(
                # Render field.
                Div([
                    Span([Text(field.label)],
                         {"style": "font-weight: bold"}
                         )]))
        return super().__init__(
            content,
        )


class Form(Div):
    def __init__(self, form):
        content = []
        self.form = form
        # form.non_field_errors
        content.append(NFErrors(form))
        # form.hidden_fields
        content.append(HiddenFields(form))
        # form.fields
        content.append(Fields(form))
        content.append(Text(f'Django Form {form.__class__.__name__}'))
        return super().__init__(
            content,
        )
