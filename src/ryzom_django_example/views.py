from django import forms
from django.urls import path, reverse
from django.views import generic

from ryzom_django.html import template
from ryzom_django_mdc import html


class ExampleDocument(html.Html):
    title = 'Secure Elections with homomorphic encryption'


# Serves to demonstrate template composition based on multi level nesting
class ExampleCard(html.Div):
    def __init__(self, *content, **context):
        super().__init__(*content, style='max-width: 20em; margin: auto')


# in general, you wouldn't go through a template_name, but since this is useful
# to design views that you import from external packages, we have this example
# here, it also shows how you can compose by nesting different layout objects
@html.template('form.html', ExampleDocument, ExampleCard)
class ExampleFormViewComponent(html.Div):
    title = 'Example form view'

    def to_html(self, view, form, **context):
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

        content += [
            html.Form(
                html.CSRFInput(view.request),
                form,
                html.MDCButton(form.submit_label),
                method='POST',
            )
        ]

        return super().to_html(*content, **context)


class ExampleForm(forms.Form):
    submit_label = 'Send'

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

    document = forms.FileField(
        widget=forms.FileInput,
        help_text='Choose a file'
    )

    select = forms.ChoiceField(
        widget=forms.Select,
        choices=(
            ('Test', (
                (1, 'the first one'),
                (2, 'the second'),
                (3, 'the thirf')
            )),
            ('Re', (
                (4, '444'),
                (5, '555')
            )),
        ),
        initial=5
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


urlpatterns = [path('', ExampleFormView.as_view())]
