from django import forms
from django.urls import path
from django.views import generic

import ryzom_mdc as html


class ExampleDocument(html.Html):
    stylesheets = [
        'https://fonts.googleapis.com/icon?family=Material+Icons',
        'https://fonts.googleapis.com/css2?family=Nanum+Pen+Script&display=swap',
        'https://unpkg.com/material-components-web@latest/dist/material-components-web.min.css',
    ]
    scripts = [
        'https://unpkg.com/material-components-web@latest/dist/material-components-web.min.js',
    ]

    def __init__(self, *content, **context):
        links = [
            html.Link(href=src, rel='stylesheet')
            for src in self.stylesheets
        ]
        scripts = [
            html.Script(src=src, type='text/javascript')
            for src in self.scripts
        ]
        scripts.append(html.Script('mdc.autoInit()', type='text/javascript'))

        super().__init__(
            html.Head(
                html.Meta(charset='utf-8'),
                html.Meta(
                    name='viewport',
                    content='width=device-width, initial-scale=1.0',
                ),
                html.Title('Secure elections with homomorphic encryption'),
                *links,
            ),
            html.Body(
                *content,
                *scripts,
                cls='mdc-typography',
            ),
        )


# Serves to demonstrate template composition based on multi level nesting
class ExampleCard(html.Div):
    def __init__(self, *content, **context):
        super().__init__(*content, style='max-width: 20em; margin: auto')


# in general, you wouldn't go through a template_name, but since this is useful
# to design views that you import from external packages, we have this example
# here, it also shows how you can compose by nesting different layout objects
@html.template('form.html', ExampleDocument, ExampleCard)
class ExampleFormViewComponent(html.Html):
    def __init__(self, *content, view, form, **context):
        # view and form come from the default context, we're spreading them as
        # nice, required variables for this template.

        # As you can imagine, having templates in Python not only gives you all
        # the programing power, but it also allows you to use a debugger
        # breakpoint() which was not possible with traditionnal templates.

        content = []

        if view.request.method == 'POST' and form.is_valid():
            content += [
                html.Div(
                    html.H3('Form post success!'),
                    html.MDCList(*[
                        html.MDCListItem(f'{key}: {value}')
                        for key, value in form.cleaned_data.items()
                    ])
                )
            ]

        content.append(
            html.Form(
                html.CSRFInput(view.request),
                form,
                method="post",
            ),
        )
        super().__init__(*content)


class ExampleForm(forms.Form):
    char = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    boolean = forms.BooleanField(required=False)
    checkboxes = forms.MultipleChoiceField(
        required=False,
        choices=(('a', 'a'), ('b', 'b')),
        widget=forms.CheckboxSelectMultiple,
    )
    datetime = forms.SplitDateTimeField(
        required=False,
        widget=forms.SplitDateTimeWidget(
            date_attrs=dict(type='date'),
            time_attrs=dict(type='time'),
        ),
    )

    # Let's override the default rendering to add a submit button
    def to_components(self):
        return html.Div(
            html.H3('Example form!'),
            super().to_components(),
            html.Div(
                html.MDCButtonOutlined('Submit'),
            )
        )


# Finally, a Django FormView, there's nothing to see here because of how well
# Ryzom integrates with Django. Of course you're free to make views that do
# some crazy Ryzom rendering, this merely shows how you would hook in the
# default Django rendering on external views that you include and do not want
# to fork: you can just override the default template with @html.template
# instead of by creating html templates.
class ExampleFormView(generic.FormView):
    template_name = 'form.html'
    form_class = ExampleForm

    def form_valid(self, form):
        # we don't have a success url, render again on form_valid
        return super().get(self.request)


urlpatterns = [
    path('', ExampleFormView.as_view())
]
