from django import forms, http
from django.urls import path, reverse
from django.views import generic

import py2js
from py2js.renderer import JS
from ryzom.components import ReactiveComponentMixin, SubscribeComponentMixin
from ryzom_django_channels.views import ReactiveMixin, register
from ryzom_django_mdc.components import *

from .models import Message, Room


class AjaxFormMixin(py2js.Mixin):
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

    def py2js(self):
        form = getElementByUuid(self._id)
        form.addEventListener('submit', self.on_form_submit)


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


class DeleteButton(Component):
    tag = 'delete-button'

    def __init__(self, *content, **attrs):
        content = content or (MDCButtonOutlined(MDCIcon('delete')),)
        super().__init__(*content, **attrs)

    class HTMLElement:
        def connectedCallback(self):
            this.addEventListener('click', this.delete.bind(this))

        async def delete(self, event):
            csrf = document.querySelector('[name="csrfmiddlewaretoken"]')

            print('url', this.attributes['delete-url'].value)
            await fetch(this.attributes['delete-url'].value, {
                method: 'delete',
                headers: {'X-CSRFTOKEN': csrf.value},
                redirect: 'manual',
            }).then(
                lambda response: print(response)
            )


class MessageItem(MDCListItem):
    def __init__(self, obj):
        self.obj = obj

        super().__init__(
            Span(obj.user or 'Anonymous', ' says: ', obj.message),
            DeleteButton(
                delete_url=reverse('message_delete', args=[self.obj.id]),
            ),
            _id=f'message-{obj.id}',
        )


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
        '/reactive/bundle.js',
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



class BundleView(generic.View):
    def get(self, *args, **kwargs):
        from ryzom.js import bundle
        response = http.HttpResponse(
                bundle('ryzom_django_channels_example.views'),
        )
        response['Content-Type'] = 'text/javascript'
        return response

    @classmethod
    def as_url(cls):
        return path('bundle.js', cls.as_view())


urlpatterns = [
    ChatView.as_url(),
    ChatDeleteView.as_url(),
    BundleView.as_url(),
]
