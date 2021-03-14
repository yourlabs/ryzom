from django import forms
from django.urls import path, reverse
from django.views import generic

from py2js.renderer import JS
from ryzom.components import ReactiveComponentMixin, SubscribeComponentMixin
from ryzom_django_channels.views import ReactiveMixin, register
from ryzom_django_mdc.components import *

from .models import Message, Room


class AjaxFormMixin:
    def render_js(self):
        def handle_submit():
            async def on_form_submit(event):
                event.preventDefault()

                form = event.target

                await fetch(form.action, {
                    'method': form.method,
                    'body': new.FormData(form)
                }).then(
                    lambda response : print(response)
                )

                form.reset()

            form = getElementByUuid(form_id)
            form.addEventListener('submit', on_form_submit)

        return JS(handle_submit, dict(form_id=self._id))


class MessageFormComponent(AjaxFormMixin, Form):
    def __init__(self, *content, view, form, **context):
        super().__init__(
            Div(
                form,
                MDCButton(form.submit_label or 'submit'),
                style='display:flex; flex-flow: row nowrap; align-items: baseline;'),
            CSRFInput(view.request),
            method='POST',
            **context)


class MessageItem(MDCListItem):
    def __init__(self, obj):
        self.obj = obj
        self.btn = MDCButtonOutlined(MDCIcon('delete'))

        super().__init__(
            Span(obj.user or 'Anonymous', ' says: ', obj.message),
            self.btn,
            _id=f'message-{obj.id}')

    def render_js(self):
        def delete_message():
            def handle_response(response):
                console.log(response.status)

            async def exec_delete(event):
                csrf = document.querySelector('[name="csrfmiddlewaretoken"]')
                request = new.Request(delete_url)
                request.headers['X-CSRFTOKEN'] = csrf.value
                request['method'] = 'delete'

                await fetch(request).then(
                    lambda response : print(response)
                )

            btn = getElementByUuid(btn_id)
            btn.addEventListener('click', exec_delete)

        return JS(delete_message, dict(
            btn_id=self.btn._id,
            delete_url=reverse('message_delete', args=[self.obj.id])))


class ChatRoom(MDCList, SubscribeComponentMixin):
    publication = 'messages'

    def __init__(self, room_id):
        self.subscribe_options['room_id'] = room_id
        super().__init__()

    @classmethod
    def get_queryset(cls, qs, opts):
        count = qs.count()
        start = max(count - 10, 0)
        return qs.filter(room__name=opts['room_id'])[start:count]


class RoomItem(MDCListItem):
    def __init__(self, room):
        super().__init__(room.name,
            _id=f'room-{room.id}',
            tag='a',
            href=f'/reactive/?room={room.name}')


class RoomForm(Div):
    def __init__(self, order_by):
        super().__init__(
            Form(
                MDCTextFieldOutlined(
                    MDCTextInput('room'), 'Room Name'),
                MDCButton('go'),
                RoomList(order_by),
            )
        )


class RoomList(MDCList, SubscribeComponentMixin):
    publication = 'rooms'

    def __init__(self, order_by):
        self.subscribe_options['order_by'] = order_by
        super().__init__()

    @classmethod
    def get_queryset(self, qs, opts):
        return qs.order_by(opts['order_by'])


class Head(Head):
    stylesheets = [
        'https://fonts.googleapis.com/icon?family=Material+Icons',
        'https://fonts.googleapis.com/css2?family=Nanum+Pen+Script&display=swap',
        'https://unpkg.com/material-components-web@latest/dist/material-components-web.min.css',
    ]

    scripts = [
        'https://unpkg.com/material-components-web@latest/dist/material-components-web.min.js',
        '/static/py2js.js',
        '/static/ryzom.js',
    ]


class Body(Body):
    stylesheets = [
        'form div, form .mdc-text-field, .mdc-list-item__text {width: 100%;}'
        + '.mdc-list-item__text {display: flex; justify-content: space-between;',
    ]

    scripts = ['mdc.autoInit();']

    def __init__(self, view, *content):
        super().__init__(*content)
        self.scripts += [view.get_token()]


class ReactiveTitle(ReactiveComponentMixin, H1):
    register = 'page_title'

    def __init__(self, room):
        super().__init__(f'Test - {room}')


@template('home')
class Home(Component):
    tag = 'html'

    def __init__(self, *content, view, form, **context):
        current_room = view.request.GET.get('room', 'general')
        super().__init__(
            Head(),
            Body(
                view,
                ReactiveTitle(''),
                A('test forms', href='form/'),
                Div(
                    Div(
                        RoomForm(
                            view.request.GET.get('order_by', 'name')),
                        style='min-width: 20%'),
                    Div(
                        ChatRoom(current_room),
                        MessageFormComponent(
                            view=view,
                            form=form,
                            style='width:100%'),
                        style='flex-grow: 1; height: 100%;'),
                    style='display:flex; flex-flow: row wrap;'),
                *content,
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
        register('page_title').update(ReactiveTitle(room))

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
]
