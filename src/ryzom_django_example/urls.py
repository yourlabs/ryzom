from django import forms
from django.urls import path, reverse
from django.views import generic

from ryzom_django.html import template
from ryzom_django.views import ReactiveMixin
from ryzom.js.renderer import JS
import ryzom_mdc as html

from .components import ChatRoom, RoomForm, MessageFormComponent
from .models import Message, Room


class ExampleDocument(html.Html):
    title = 'Custom title'


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

        content.append(html.SimpleForm(view, form))
        super().__init__(*content)


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


class Head(html.Head):
    stylesheets = [
        'https://fonts.googleapis.com/icon?family=Material+Icons',
        'https://fonts.googleapis.com/css2?family=Nanum+Pen+Script&display=swap',
        'https://unpkg.com/material-components-web@latest/dist/material-components-web.min.css',
    ]

    scripts = [
        'https://unpkg.com/material-components-web@latest/dist/material-components-web.min.js',
        '/static/ryzom/js/py-builtins.js',
        '/static/ryzom/js/ryzom.js',
    ]


class Body(html.Body):
    stylesheets = [
        'form div, form .mdc-text-field, .mdc-list-item__text {width: 100%;}'
        + '.mdc-list-item__text {display: flex; justify-content: space-between;',
    ]

    def __init__(self, view, *content):
        super().__init__(*content)
        self.scripts += [
            'mdc.autoInit();',
            view.get_token()
        ]


@template('home')
class Home(html.Component):
    tag='html'
    def __init__(self, *content, view, form, **context):
        super().__init__(
            Head(),
            Body(view,
                html.H1('Test'),
                html.A('test forms', href='form/'),
                html.Div(
                    html.Div(
                        RoomForm(
                            view.request.GET.get('order_by', 'name')),
                        style='min-width: 20%'),
                    html.Div(
                        ChatRoom(view.request.GET.get('room', 'general')),
                        MessageFormComponent(
                            view=view,
                            form=form,
                            style='width:100%'),
                        style='flex-grow: 1; height: 100%;'),
                    style='display:flex; flex-flow: row wrap;')
            )
        )


class MessageForm(forms.ModelForm):
    submit_label = 'Send'

    message = forms.CharField(
        required=True,
        help_text='type your message here')

    class Meta:
        model = Message
        fields = ['message']


class ChatView(ReactiveMixin, generic.CreateView):
    template_name = 'home'
    form_class = MessageForm

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user

        room = self.request.GET.get('room', 'general')
        room_obj, _ = Room.objects.get_or_create(name=room)

        form.instance.room = room_obj

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('home')

    @classmethod
    def as_url(cls):
        return path('', cls.as_view(), name='home')


class ChatDeleteView(generic.DeleteView):
    model = Message

    def dispatch(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('home')

    @classmethod
    def as_url(cls):
        return path('message/<pk>/delete', cls.as_view(), name='message_delete')


urlpatterns = [
    ChatView.as_url(),
    ChatDeleteView.as_url(),
    path('form/', ExampleFormView.as_view())
]
