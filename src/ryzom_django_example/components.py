from django.urls import reverse
from ryzom_mdc import *
from ryzom.components import SubscribeComponentMixin
from ryzom.js.renderer import JS

from .models import Message


class AjaxFormMixin:
    def render_js(self):
        def handle_submit():
            def handle_response(response):
                console.log(response.status)

            def on_form_submit(event):
                event.preventDefault()

                form = event.target
                data = _new(object)
                setattr(data, 'method', form.method)
                setattr(data, 'body', _new(FormData, form))

                form.reset()

                _await(fetch, form.action, data).then(handle_response)

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

            def exec_delete(event):
                csrf = document.querySelector('[name="csrfmiddlewaretoken"]')
                request = _new(Request, delete_url)
                setattr(request.headers, 'X-CSRFTOKEN', csrf.value)
                setattr(request, 'method', 'delete')

                _await(fetch, request).then(handle_response)

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
            href=f'/?room={room.name}')


class RoomForm(Div):
    def __init__(self, order_by):
        super().__init__(
            Form(
                MDCTextFieldOutlined(
                    MDCTextInput('room-name')),
                MDCButton('go'),
                RoomList(order_by))
        )

    def render_js(self):
        def form_submit_handler():
            def go_to_room(event):
                event.preventDefault()
                room_name = event.target.querySelector('input').value
                setattr(document.location, 'href', '/?room=' + room_name)

            form = getElementByUuid(_id)
            form.addEventListener('submit', go_to_room)

        return JS(form_submit_handler, dict(_id=self._id))


class RoomList(MDCList, SubscribeComponentMixin):
    publication = 'rooms'

    def __init__(self, order_by):
        self.subscribe_options['order_by'] = order_by
        super().__init__()

    @classmethod
    def get_queryset(self, qs, opts):
        return qs.order_by(opts['order_by'])
