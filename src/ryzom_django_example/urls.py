from django import forms
from django.urls import path
from django.views import generic

from ryzom import html


# in general, you wouldn't go through a template_name, but since this is useful
# to design views that you import from external packages, we have this example
# here
@html.template('home.html')
class ExampleFormViewComponent(html.Html):
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
            html.Body(context['form'], *scripts),
        )


class ExampleForm(forms.Form):
    char = forms.CharField()
    boolean = forms.BooleanField()
    #checkboxes = forms.MultipleChoiceField(
    #    choices=(('a', 'a'), ('b', 'b')),
    #    widget=forms.CheckboxSelectMultiple,
    #)

class ExampleFormView(generic.FormView):
    template_name = 'home.html'
    form_class = ExampleForm


urlpatterns = [
    path('', ExampleFormView.as_view())
]
