from django import forms
from django.urls import path
from django.views import generic

from ryzom.js.renderer import JS
import ryzom_mdc as html


class ExampleDocument(html.Html):
    stylesheets = [
        'https://fonts.googleapis.com/icon?family=Material+Icons',
        'https://fonts.googleapis.com/css2?family=Nanum+Pen+Script&display=swap',
        'https://unpkg.com/material-components-web@latest/dist/material-components-web.min.css',
    ]
    scripts = [
        'https://unpkg.com/material-components-web@latest/dist/material-components-web.min.js',
        'static/ryzom/js/py-builtins.js',
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

        body = html.Body(
            *content,
            cls='mdc-typography',
        )

        scripts.append(html.Script(body.render_js_tree(), type='text/javascript'))

        body.addchildren(scripts)

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
            body
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
    char = forms.CharField(
        help_text='Non required example text input',
    )
    email = forms.EmailField(
        help_text='Valid email required',
    )
    boolean = forms.BooleanField(
        help_text='Required boolean!',
    )
    checkboxes = forms.MultipleChoiceField(
        choices=(('a', 'a'), ('b', 'b')),
        widget=forms.CheckboxSelectMultiple,
        help_text='Required checkbox multiple',
    )
    datetime = forms.SplitDateTimeField(
        widget=forms.SplitDateTimeWidget(
            date_attrs=dict(type='date'),
            time_attrs=dict(type='time'),
        ),
        help_text='Required help text',
    )
    textarea = forms.CharField(
        widget=forms.Textarea,
        help_text='This is the help text'
    )

    # Let's override the default rendering to add a submit button
    def to_component(self):
        class FormDiv(html.Div):
            def render_js(self):
                def setvar():
                    setattr(window, 'toto', 'toto')

                return JS(setvar)

        return FormDiv(
            html.H3('Example form!'),
            super().to_component(),
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
