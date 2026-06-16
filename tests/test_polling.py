import json
import functools
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from django import views
from django.conf import settings
from django.test import RequestFactory, TestCase
from django.contrib.auth.models import AnonymousUser

from ryzom import html

if settings.CHANNELS_ENABLE:
    from ryzom_django_channels.models import Client, Registration
    from ryzom_django_channels.views import ReactiveMixin, RegisterManager, register
    from ryzom_django_channels import messagequeue
    from ryzom_django_channels.ddp import (
        _client_is_available, _translate_ddp, _send_to_client,
        send_insert, send_change, send_remove,
    )

skip_reactive = pytest.mark.skipif(
    not settings.CHANNELS_ENABLE, reason='Reactive disabled')

factory = RequestFactory()


def req(url='/', user=None):
    request = factory.get(url)
    request.user = user or AnonymousUser()
    return request


def db_reactive(func):
    @skip_reactive
    @pytest.mark.django_db
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def view():
    class MyView(ReactiveMixin, views.generic.View):
        pass
    v = MyView()
    v.setup(req())
    return v


@pytest.fixture
def client_ws(view):
    '''Create a Client with WS transport (default).'''
    meta = view.get_token()
    token = meta.attrs['content']
    return Client.objects.get(token=token)


@pytest.fixture
def client_poll(view):
    '''Create a Client and switch to poll transport.'''
    meta = view.get_token()
    token = meta.attrs['content']
    client = Client.objects.get(token=token)
    client.transport = 'poll'
    client.save()
    return client


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

@db_reactive
def test_client_transport_default(client_ws):
    assert client_ws.transport == 'ws'


@db_reactive
def test_client_transport_poll(client_poll):
    assert client_poll.transport == 'poll'


@db_reactive
def test_client_transport_choices():
    expected = [('ws', 'WebSocket'), ('poll', 'HTTP Polling')]
    assert Client.TRANSPORT_CHOICES == expected


# ---------------------------------------------------------------------------
# Meta tag / ReactiveMixin tests
# ---------------------------------------------------------------------------

@db_reactive
def test_get_token_has_transport_attr(view):
    meta = view.get_token()
    assert 'data-transport' in meta.attrs
    assert 'data-poll-url' in meta.attrs


@db_reactive
def test_get_token_default_transport(view):
    meta = view.get_token()
    # Default RYZOM_TRANSPORT is 'auto'
    assert meta.attrs['data-transport'] == 'auto'


@db_reactive
def test_get_token_poll_url_default(view):
    meta = view.get_token()
    assert meta.attrs['data-poll-url'] == '/ddp/'


@db_reactive
def test_get_token_poll_transport_sets_client(view):
    with patch.object(settings, 'RYZOM_TRANSPORT', 'poll', create=True):
        meta = view.get_token()
        token = meta.attrs['content']
        client = Client.objects.get(token=token)
        assert client.transport == 'poll'
        assert meta.attrs['data-transport'] == 'poll'


# ---------------------------------------------------------------------------
# Message queue tests
# ---------------------------------------------------------------------------

@db_reactive
def test_push_and_drain(client_poll):
    msg = {'type': 'DDP', 'params': {'type': 'insert', 'params': {'id': '1'}}}
    messagequeue.push_message(client_poll.token, msg)
    messages = messagequeue.drain_messages(client_poll.token)
    assert len(messages) == 1
    assert messages[0] == msg


@db_reactive
def test_drain_empties_queue(client_poll):
    msg = {'type': 'DDP', 'params': {'type': 'insert', 'params': {'id': '1'}}}
    messagequeue.push_message(client_poll.token, msg)
    messagequeue.drain_messages(client_poll.token)
    # Second drain should return empty
    messages = messagequeue.drain_messages(client_poll.token)
    assert messages == []


@db_reactive
def test_drain_multiple_messages(client_poll):
    for i in range(5):
        messagequeue.push_message(
            client_poll.token,
            {'type': 'DDP', 'params': {'type': 'insert', 'params': {'id': str(i)}}}
        )
    messages = messagequeue.drain_messages(client_poll.token)
    assert len(messages) == 5
    assert messages[0]['params']['params']['id'] == '0'
    assert messages[4]['params']['params']['id'] == '4'


@db_reactive
def test_clear_queue(client_poll):
    messagequeue.push_message(
        client_poll.token,
        {'type': 'DDP', 'params': {'type': 'test'}}
    )
    messagequeue.clear_queue(client_poll.token)
    messages = messagequeue.drain_messages(client_poll.token)
    assert messages == []


@db_reactive
def test_drain_empty_queue(client_poll):
    messages = messagequeue.drain_messages(client_poll.token)
    assert messages == []


# ---------------------------------------------------------------------------
# DDP translation tests
# ---------------------------------------------------------------------------

@db_reactive
def test_translate_ddp_inserted():
    instance = {'id': 'abc', 'tag': 'div'}
    result = _translate_ddp({'type': 'inserted', 'instance': instance})
    assert result == {
        'type': 'DDP',
        'params': {'type': 'insert', 'params': instance},
    }


@db_reactive
def test_translate_ddp_changed():
    instance = {'id': 'abc', 'tag': 'div'}
    result = _translate_ddp({'type': 'changed', 'instance': instance})
    assert result == {
        'type': 'DDP',
        'params': {'type': 'change', 'params': instance},
    }


@db_reactive
def test_translate_ddp_removed():
    result = _translate_ddp({
        'type': 'removed', 'id': 'comp-1', 'parent': 'parent-1'
    })
    assert result == {
        'type': 'DDP',
        'params': {
            'type': 'remove',
            'params': {'id': 'comp-1', 'parent': 'parent-1'},
        },
    }


@db_reactive
def test_translate_ddp_unknown():
    result = _translate_ddp({'type': 'unknown'})
    assert result is None


# ---------------------------------------------------------------------------
# _client_is_available tests
# ---------------------------------------------------------------------------

@db_reactive
def test_client_is_available_none():
    assert _client_is_available(None) is False


@db_reactive
def test_client_is_available_ws_no_channel(client_ws):
    client_ws.channel = ''
    assert _client_is_available(client_ws) is False


@db_reactive
def test_client_is_available_ws_with_channel(client_ws):
    client_ws.channel = 'some.channel.name'
    assert _client_is_available(client_ws) is True


@db_reactive
def test_client_is_available_poll_no_channel(client_poll):
    # Poll clients are always available regardless of channel
    client_poll.channel = ''
    assert _client_is_available(client_poll) is True


@db_reactive
def test_client_is_available_poll_with_channel(client_poll):
    client_poll.channel = 'some.channel'
    assert _client_is_available(client_poll) is True


# ---------------------------------------------------------------------------
# _send_to_client tests
# ---------------------------------------------------------------------------

@db_reactive
def test_send_to_client_poll_pushes_to_redis(client_poll):
    data = {
        'type': 'handle.ddp',
        'params': {
            'type': 'inserted',
            'instance': {'id': 'x', 'tag': 'div'},
        },
    }
    _send_to_client(client_poll, data)
    messages = messagequeue.drain_messages(client_poll.token)
    assert len(messages) == 1
    assert messages[0]['type'] == 'DDP'
    assert messages[0]['params']['type'] == 'insert'
    assert messages[0]['params']['params']['id'] == 'x'


@db_reactive
def test_send_to_client_ws_uses_channel_layer(client_ws):
    client_ws.channel = 'test.channel'
    data = {
        'type': 'handle.ddp',
        'params': {'type': 'inserted', 'instance': {'id': 'x'}},
    }
    with patch('ryzom_django_channels.ddp.get_channel_layer') as mock_gcl:
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock()
        mock_gcl.return_value = mock_channel
        _send_to_client(client_ws, data)
        mock_channel.send.assert_called_once()


# ---------------------------------------------------------------------------
# Polling view tests
# ---------------------------------------------------------------------------

@db_reactive
def test_poll_send_ping(client_poll):
    from django.test import Client as DjangoClient
    c = DjangoClient()
    resp = c.post(
        '/ddp/send/',
        data=json.dumps({'id': '123', 'type': 'ping', 'params': {}}),
        content_type='application/json',
        HTTP_X_RYZOM_TOKEN=client_poll.token,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['type'] == 'pong'
    assert data['id'] == '123'


@db_reactive
def test_poll_send_no_token():
    from django.test import Client as DjangoClient
    c = DjangoClient()
    resp = c.post(
        '/ddp/send/',
        data=json.dumps({'id': '1', 'type': 'ping', 'params': {}}),
        content_type='application/json',
    )
    assert resp.status_code == 401


@db_reactive
def test_poll_send_invalid_token():
    from django.test import Client as DjangoClient
    c = DjangoClient()
    resp = c.post(
        '/ddp/send/',
        data=json.dumps({'id': '1', 'type': 'ping', 'params': {}}),
        content_type='application/json',
        HTTP_X_RYZOM_TOKEN='bogus-token',
    )
    assert resp.status_code == 401


@db_reactive
def test_poll_send_bad_json(client_poll):
    from django.test import Client as DjangoClient
    c = DjangoClient()
    resp = c.post(
        '/ddp/send/',
        data='not json',
        content_type='application/json',
        HTTP_X_RYZOM_TOKEN=client_poll.token,
    )
    assert resp.status_code == 400


@db_reactive
def test_poll_send_missing_id(client_poll):
    from django.test import Client as DjangoClient
    c = DjangoClient()
    resp = c.post(
        '/ddp/send/',
        data=json.dumps({'type': 'ping', 'params': {}}),
        content_type='application/json',
        HTTP_X_RYZOM_TOKEN=client_poll.token,
    )
    assert resp.status_code == 400


@db_reactive
def test_poll_send_bad_type(client_poll):
    from django.test import Client as DjangoClient
    c = DjangoClient()
    resp = c.post(
        '/ddp/send/',
        data=json.dumps({'id': '1', 'type': 'badtype', 'params': {}}),
        content_type='application/json',
        HTTP_X_RYZOM_TOKEN=client_poll.token,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['type'] == 'Error'
    assert data['params']['name'] == 'Bad message type'


@db_reactive
def test_poll_send_method_type_rejected(client_poll):
    '''method type was removed and should now be rejected.'''
    from django.test import Client as DjangoClient
    c = DjangoClient()
    resp = c.post(
        '/ddp/send/',
        data=json.dumps({
            'id': '1', 'type': 'method',
            'params': {'name': 'anything', 'params': {}},
        }),
        content_type='application/json',
        HTTP_X_RYZOM_TOKEN=client_poll.token,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['type'] == 'Error'
    assert data['params']['name'] == 'Bad message type'


@db_reactive
def test_poll_send_subscribe_type_rejected(client_poll):
    '''subscribe type was removed and should now be rejected.'''
    from django.test import Client as DjangoClient
    c = DjangoClient()
    resp = c.post(
        '/ddp/send/',
        data=json.dumps({
            'id': '1', 'type': 'subscribe',
            'params': {'name': 'test', 'sub_id': 'x', 'parent_id': 'y'},
        }),
        content_type='application/json',
        HTTP_X_RYZOM_TOKEN=client_poll.token,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['type'] == 'Error'
    assert data['params']['name'] == 'Bad message type'


@db_reactive
def test_poll_send_missing_params(client_poll):
    from django.test import Client as DjangoClient
    c = DjangoClient()
    resp = c.post(
        '/ddp/send/',
        data=json.dumps({'id': '1', 'type': 'ping'}),
        content_type='application/json',
        HTTP_X_RYZOM_TOKEN=client_poll.token,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['type'] == 'Error'
    assert data['params']['name'] == 'Bad format'


@db_reactive
def test_poll_send_login_type_rejected(client_poll):
    '''login type was removed and should now be rejected.'''
    from django.test import Client as DjangoClient
    c = DjangoClient()
    resp = c.post(
        '/ddp/send/',
        data=json.dumps({'id': '1', 'type': 'login', 'params': {'username': 'a', 'password': 'b'}}),
        content_type='application/json',
        HTTP_X_RYZOM_TOKEN=client_poll.token,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['type'] == 'Error'
    assert data['params']['name'] == 'Bad message type'


@db_reactive
def test_poll_send_logout_type_rejected(client_poll):
    '''logout type was removed and should now be rejected.'''
    from django.test import Client as DjangoClient
    c = DjangoClient()
    resp = c.post(
        '/ddp/send/',
        data=json.dumps({'id': '1', 'type': 'logout', 'params': {}}),
        content_type='application/json',
        HTTP_X_RYZOM_TOKEN=client_poll.token,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['type'] == 'Error'
    assert data['params']['name'] == 'Bad message type'


# ---------------------------------------------------------------------------
# PollReceiveView tests
# ---------------------------------------------------------------------------

@db_reactive
def test_poll_receive_empty(client_poll):
    from django.test import Client as DjangoClient
    c = DjangoClient()
    resp = c.get(
        '/ddp/poll/',
        HTTP_X_RYZOM_TOKEN=client_poll.token,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['messages'] == []


@db_reactive
def test_poll_receive_with_messages(client_poll):
    from django.test import Client as DjangoClient
    msg1 = {'type': 'DDP', 'params': {'type': 'insert', 'params': {'id': '1'}}}
    msg2 = {'type': 'DDP', 'params': {'type': 'change', 'params': {'id': '2'}}}
    messagequeue.push_message(client_poll.token, msg1)
    messagequeue.push_message(client_poll.token, msg2)

    c = DjangoClient()
    resp = c.get(
        '/ddp/poll/',
        HTTP_X_RYZOM_TOKEN=client_poll.token,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data['messages']) == 2
    assert data['messages'][0] == msg1
    assert data['messages'][1] == msg2


@db_reactive
def test_poll_receive_drains(client_poll):
    from django.test import Client as DjangoClient
    messagequeue.push_message(
        client_poll.token,
        {'type': 'DDP', 'params': {'type': 'test'}},
    )

    c = DjangoClient()
    c.get('/ddp/poll/', HTTP_X_RYZOM_TOKEN=client_poll.token)
    # Second poll should be empty
    resp = c.get('/ddp/poll/', HTTP_X_RYZOM_TOKEN=client_poll.token)
    assert resp.json()['messages'] == []


@db_reactive
def test_poll_receive_no_token():
    from django.test import Client as DjangoClient
    c = DjangoClient()
    resp = c.get('/ddp/poll/')
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# TransportSwitchView tests
# ---------------------------------------------------------------------------

@db_reactive
def test_transport_switch(client_ws):
    from django.test import Client as DjangoClient
    assert client_ws.transport == 'ws'
    c = DjangoClient()
    resp = c.post(
        '/ddp/switch/',
        data='{}',
        content_type='application/json',
        HTTP_X_RYZOM_TOKEN=client_ws.token,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'ok'
    assert data['transport'] == 'poll'

    client_ws.refresh_from_db()
    assert client_ws.transport == 'poll'


@db_reactive
def test_transport_switch_no_token():
    from django.test import Client as DjangoClient
    c = DjangoClient()
    resp = c.post(
        '/ddp/switch/',
        data='{}',
        content_type='application/json',
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# DDP send_* with poll transport tests
# ---------------------------------------------------------------------------

@db_reactive
def test_send_insert_poll(client_poll):
    '''send_insert should push translated message to Redis for poll clients.'''
    mock_sub = MagicMock()
    mock_sub.client = client_poll
    mock_sub.subscriber_id = 'parent-1'
    # qs holds the (string) pks in display order; the real signal flow fills it
    # via get_queryset() before send_*. MagicMock bypasses the queryset setter,
    # so set qs directly (see _position_map in ddp.py).
    mock_sub.qs = ['42']

    mock_instance = MagicMock()
    mock_instance.pk = 42

    mock_tmpl_instance = MagicMock()
    mock_tmpl_instance.to_obj.return_value = {'id': 'comp-1', 'tag': 'div'}
    mock_tmpl = MagicMock(return_value=mock_tmpl_instance)

    send_insert(mock_sub, mock_tmpl, mock_instance)

    messages = messagequeue.drain_messages(client_poll.token)
    assert len(messages) == 1
    assert messages[0]['type'] == 'DDP'
    assert messages[0]['params']['type'] == 'insert'
    assert messages[0]['params']['params']['id'] == 'comp-1'


@db_reactive
def test_send_change_poll(client_poll):
    '''send_change should push translated message to Redis for poll clients.'''
    mock_sub = MagicMock()
    mock_sub.client = client_poll
    mock_sub.subscriber_id = 'parent-1'
    mock_sub.qs = ['42']

    mock_instance = MagicMock()
    mock_instance.pk = 42

    mock_tmpl_instance = MagicMock()
    mock_tmpl_instance.to_obj.return_value = {'id': 'comp-1', 'tag': 'span'}
    mock_tmpl = MagicMock(return_value=mock_tmpl_instance)

    send_change(mock_sub, mock_tmpl, mock_instance)

    messages = messagequeue.drain_messages(client_poll.token)
    assert len(messages) == 1
    assert messages[0]['type'] == 'DDP'
    assert messages[0]['params']['type'] == 'change'


@db_reactive
def test_send_remove_poll(client_poll):
    '''send_remove should push translated message to Redis for poll clients.'''
    mock_sub = MagicMock()
    mock_sub.client = client_poll
    mock_sub.subscriber_id = 'parent-1'

    mock_instance = MagicMock()

    mock_tmpl_instance = MagicMock()
    mock_tmpl_instance.id = 'comp-1'
    mock_tmpl = MagicMock(return_value=mock_tmpl_instance)
    # No dom_id classmethod on this template: exercise the instantiation
    # fallback (a bare MagicMock auto-creates a truthy dom_id attribute).
    mock_tmpl.dom_id = None

    send_remove(mock_sub, mock_tmpl, mock_instance)

    messages = messagequeue.drain_messages(client_poll.token)
    assert len(messages) == 1
    assert messages[0]['type'] == 'DDP'
    assert messages[0]['params']['type'] == 'remove'
    assert messages[0]['params']['params']['id'] == 'comp-1'
    assert messages[0]['params']['params']['parent'] == 'parent-1'


@db_reactive
def test_send_remove_poll_dom_id(client_poll):
    '''send_remove should prefer the template's dom_id classmethod, never
    instantiating the template (which may crash on a deleted row).'''
    mock_sub = MagicMock()
    mock_sub.client = client_poll
    mock_sub.subscriber_id = 'parent-1'

    mock_tmpl = MagicMock()
    mock_tmpl.dom_id = lambda instance: 'row-42'
    mock_tmpl.side_effect = AssertionError('template must not be rendered')

    send_remove(mock_sub, mock_tmpl, MagicMock())

    messages = messagequeue.drain_messages(client_poll.token)
    assert len(messages) == 1
    assert messages[0]['params']['params']['id'] == 'row-42'


@db_reactive
def test_send_insert_skips_unavailable():
    '''send_insert should silently return when client is unavailable.'''
    mock_sub = MagicMock()
    mock_sub.client = None
    send_insert(mock_sub, MagicMock(), MagicMock())
    # No exception = pass


@db_reactive
def test_send_insert_skips_ws_no_channel(client_ws):
    '''send_insert should skip WS client with empty channel.'''
    client_ws.channel = ''
    mock_sub = MagicMock()
    mock_sub.client = client_ws
    with patch('ryzom_django_channels.ddp.get_channel_layer') as mock_gcl:
        send_insert(mock_sub, MagicMock(), MagicMock())
        mock_gcl.assert_not_called()


# ---------------------------------------------------------------------------
# RegisterManager poll transport tests
# ---------------------------------------------------------------------------

@db_reactive
def test_register_manager_send_poll(client_poll):
    '''RegisterManager._send_poll should push DDP change to Redis queue.'''
    mock_content = MagicMock()
    mock_content.to_obj.return_value = {'id': 'reg-1', 'tag': 'div', 'content': []}

    manager = RegisterManager(Registration.objects.none())
    manager._send_poll(client_poll, mock_content)

    messages = messagequeue.drain_messages(client_poll.token)
    assert len(messages) == 1
    assert messages[0]['type'] == 'DDP'
    assert messages[0]['params']['type'] == 'change'
    assert messages[0]['params']['params']['id'] == 'reg-1'


@db_reactive
def test_register_replace_detached_ws_drops_push_no_thread():
    '''A refresh to a detached ws client must not push anything (the reload
    on reconnect delivers fresh state) and must not spawn a thread — it only
    flags resync. Regression: defer()/wait() were removed.'''
    from ryzom_django_channels.views import RegisterManager
    from ryzom_django_channels.models import Client, Registration
    import threading

    client = Client.objects.create(
        token='detached-ws', channel='', transport='ws', needs_resync=False)
    reg = Registration.objects.create(
        name='r', client=client, subscriber_id='s', subscriber_parent='p',
        subscriber_module='ryzom_django_channels_example.models',
        subscriber_class='Room')

    manager = RegisterManager(Registration.objects.filter(pk=reg.pk))
    assert not hasattr(manager, 'defer') and not hasattr(manager, 'wait')

    before = threading.active_count()
    # _replace renders the content_class; use a trivial stub so we don't need
    # a real component — the point is that nothing is sent and no thread runs.
    sent = []
    manager._send = lambda ch, content: sent.append(content)
    manager._send_poll = lambda c, content: sent.append(content)

    class _Stub:
        def __init__(self, *a, **k):
            self.id = None
            self.parent = None

    manager._replace(reg, _Stub)

    assert sent == []
    assert threading.active_count() == before
    client.refresh_from_db()
    assert client.needs_resync is True


# ---------------------------------------------------------------------------
# URL routing tests
# ---------------------------------------------------------------------------

@db_reactive
def test_urls_resolve():
    from django.urls import resolve
    assert resolve('/ddp/send/').url_name == 'ryzom-poll-send'
    assert resolve('/ddp/poll/').url_name == 'ryzom-poll-receive'
    assert resolve('/ddp/switch/').url_name == 'ryzom-poll-switch'


# ---------------------------------------------------------------------------
# End-to-end: send_* → poll endpoint round-trip
# ---------------------------------------------------------------------------

@db_reactive
def test_end_to_end_insert_then_poll(client_poll):
    '''
    Simulate the full flow: signal triggers send_insert for a poll client,
    then the client polls and receives the DDP insert message.
    '''
    from django.test import Client as DjangoClient

    mock_sub = MagicMock()
    mock_sub.client = client_poll
    mock_sub.subscriber_id = 'parent-e2e'
    mock_sub.qs = ['1']

    mock_instance = MagicMock()
    mock_instance.pk = 1

    mock_tmpl_instance = MagicMock()
    mock_tmpl_instance.to_obj.return_value = {
        'id': 'e2e-comp', 'tag': 'div', 'content': 'hello'
    }
    mock_tmpl = MagicMock(return_value=mock_tmpl_instance)

    # Trigger the server-side send
    send_insert(mock_sub, mock_tmpl, mock_instance)

    # Poll to receive
    c = DjangoClient()
    resp = c.get('/ddp/poll/', HTTP_X_RYZOM_TOKEN=client_poll.token)
    data = resp.json()

    assert len(data['messages']) == 1
    msg = data['messages'][0]
    assert msg['type'] == 'DDP'
    assert msg['params']['type'] == 'insert'
    assert msg['params']['params']['id'] == 'e2e-comp'
    assert msg['params']['params']['content'] == 'hello'


@db_reactive
def test_end_to_end_change_then_poll(client_poll):
    from django.test import Client as DjangoClient

    mock_sub = MagicMock()
    mock_sub.client = client_poll
    mock_sub.subscriber_id = 'parent-e2e'
    mock_sub.qs = ['2']

    mock_instance = MagicMock()
    mock_instance.pk = 2

    mock_tmpl_instance = MagicMock()
    mock_tmpl_instance.to_obj.return_value = {'id': 'e2e-change', 'tag': 'span'}
    mock_tmpl = MagicMock(return_value=mock_tmpl_instance)

    send_change(mock_sub, mock_tmpl, mock_instance)

    c = DjangoClient()
    resp = c.get('/ddp/poll/', HTTP_X_RYZOM_TOKEN=client_poll.token)
    msg = resp.json()['messages'][0]
    assert msg['params']['type'] == 'change'


@db_reactive
def test_end_to_end_remove_then_poll(client_poll):
    from django.test import Client as DjangoClient

    mock_sub = MagicMock()
    mock_sub.client = client_poll
    mock_sub.subscriber_id = 'parent-e2e'

    mock_instance = MagicMock()
    mock_tmpl_instance = MagicMock()
    mock_tmpl_instance.id = 'e2e-rm'
    mock_tmpl = MagicMock(return_value=mock_tmpl_instance)
    mock_tmpl.dom_id = None

    send_remove(mock_sub, mock_tmpl, mock_instance)

    c = DjangoClient()
    resp = c.get('/ddp/poll/', HTTP_X_RYZOM_TOKEN=client_poll.token)
    msg = resp.json()['messages'][0]
    assert msg['params']['type'] == 'remove'
    assert msg['params']['params']['id'] == 'e2e-rm'
    assert msg['params']['params']['parent'] == 'parent-e2e'
