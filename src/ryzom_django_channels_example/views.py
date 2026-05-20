from django import forms, http
from django.urls import path, reverse
from django.views import generic
from django.utils.safestring import mark_safe

import py2js
from py2js.renderer import JS
from ryzom_django_channels.components import (
    ReactiveComponentMixin,
    SubscribeComponentMixin,
    model_template
)
from ryzom_django_channels.views import ReactiveMixin, register
from ryzom_django_mdc.html import *

from .models import Message, Room


class AjaxForm(Component):
    """
    Wrapper component for forms that submits via AJAX.
    Wraps the native <form> to preserve its functionality while adding AJAX behavior.
    """
    tag = 'ajax-form'

    class HTMLElement:
        def connectedCallback(self):
            window.addEventListener('load', this.init.bind(this))

        def init(self):
            this.form = this.querySelector('form')
            if this.form:
                this.form.addEventListener('submit', this.on_form_submit.bind(this))

        async def on_form_submit(self, event):
            event.preventDefault()
            form = event.target
            await fetch(form.action, {
                'method': form.method,
                'body': new.FormData(form)
            }).then(
                lambda response: print(response)
            )
            form.reset()


class MessageFormComponent(AjaxForm):
    """Form component wrapped with AjaxForm for AJAX submission."""
    def __init__(self, *content, view, form, **context):
        super().__init__(
            Form(
                Div(
                    form,
                    MDCButton(form.submit_label or 'submit'),
                    style='display:flex; flex-flow: row nowrap; align-items: baseline;'),
                CSRFInput(view.request),
                method='POST',
            ),
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


@model_template('message-item')
class MessageItem(MDCListItem):
    def __init__(self, obj):
        self.obj = obj

        username = obj.user.username if obj.user else 'Anonymous'

        super().__init__(
            Span(username, ' says: ', obj.message),
            DeleteButton(
                delete_url=reverse('message_delete', args=[self.obj.id]),
            ),
            id=f'message-{obj.id}',
        )


class ChatRoom(SubscribeComponentMixin, MDCList):
    publication = 'messages'
    model_template = 'message-item'

    def __init__(self, room_id):
        self.subscribe_options = dict(room_id=room_id)
        super().__init__()

    @classmethod
    def get_queryset(cls, user, qs, opts):
        room_messages = qs.filter(room__name=opts['room_id']).order_by('created')
        count = room_messages.count()
        start = max(count - 10, 0)
        rm = room_messages[start:count]
        return rm


@model_template('room-item')
class RoomItem(MDCListItem):
    def __init__(self, room):
        super().__init__(
            room.name,
            id=f'room-{room.id}',
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


class RoomList(SubscribeComponentMixin, MDCList):
    publication = 'rooms'
    model_template = 'room-item'

    def __init__(self, order_by):
        self.subscribe_options = dict(order_by=order_by)
        super().__init__()

    @classmethod
    def get_queryset(self, user, qs, opts):
        return qs.order_by(opts['order_by'])


class Body(Body):
    def __init__(self, *content, **context):
        super().__init__(
            Style(
                'form div, form .mdc-text-field, .mdc-list-item__text {width: 100%;}'
                + '.mdc-list-item__text {display: flex; justify-content: space-between;',
            ),
            *content,
        )


class ReactiveTitle(ReactiveComponentMixin, H1):
    register = 'page_title'

    def __init__(self, room, **kwargs):
        msg_count = 0
        name = ''

        if room:
            msg_count = room.message_set.count()
            name = room.name

        super().__init__(f'Test - {name}', f' - {msg_count}' if msg_count else None)


@template('home')
class Home(Html):
    scripts = ['/static/ryzom.js']
    body_class = Body

    def to_html(self, *content, view, form, **context):
        current_room_name = view.request.GET.get('room', 'general')
        current_room = Room.objects.filter(name=current_room_name).first()

        head, body = content

        body.addchildren([
            ReactiveTitle(current_room),
            A('test forms', href='form/'),
            Div(style='display:flex; flex-flow: row wrap;')(
                Div(style='min-width: 20%')(
                    RoomForm(view.request.GET.get('order_by', 'name')),
                ),
                Div(style='flex-grow: 1; height: 100%;')(
                    ChatRoom(current_room_name),
                    message_form=MessageFormComponent(
                        style='width:100%'
                        view=view,
                        form=form,
                    ),
                ),
            ),
            Script(mark_safe(view.get_token())),
            Script('mdc.autoInit();'),
        ])

        return super().to_html(
            head,
            body,
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

        self.object = form.save()

        register('page_title').refresh(room_obj)

        return http.HttpResponse()

    @classmethod
    def as_url(cls):
        return path('', cls.as_view(), name='home')


class ChatDeleteView(generic.DeleteView):
    model = Message

    def dispatch(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def get_success_url(self):
        msg = self.get_object()
        room = msg.room
        message_count = msg.room.message_set.count() - 1
        register('page_title').refresh(room)

        if not message_count and room.name != 'general':
            room.delete()

        return reverse('home')

    @classmethod
    def as_url(cls):
        return path('message/<pk>/delete', cls.as_view(), name='message_delete')


urlpatterns = [
    ChatView.as_url(),
    ChatDeleteView.as_url(),
]
