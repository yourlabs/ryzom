'''
HTTP polling views for DDP protocol fallback.

These views provide the same DDP protocol over regular HTTP requests
when WebSockets are unavailable (corporate firewalls, restricted
environments).

All views authenticate via X-Ryzom-Token header.
'''
import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from ryzom_django_channels.messagequeue import drain_messages
from ryzom_django_channels.models import Client


def _get_client(request):
    '''Look up client by X-Ryzom-Token header.'''
    token = request.headers.get('X-Ryzom-Token', '')
    if not token:
        return None
    return Client.objects.filter(token=token).first()


@method_decorator(csrf_exempt, name='dispatch')
class PollSendView(View):
    '''
    POST /ddp/send/ — receives DDP commands from poll clients.

    Mirrors Consumer's recv_* handler logic, returning JSON responses
    directly instead of sending through WebSocket.
    '''

    def post(self, request):
        client = _get_client(request)
        if not client:
            return JsonResponse(
                {'type': 'Error', 'params': {'name': 'Unauthorized',
                 'message': 'Invalid or missing token'}},
                status=401,
            )

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse(
                {'type': 'Error', 'params': {'name': 'Bad request',
                 'message': 'Invalid JSON'}},
                status=400,
            )

        msg_id = data.get('id')
        if not msg_id:
            return JsonResponse(
                {'type': 'Error', 'params': {'name': 'Bad message',
                 'message': 'message id not found'}},
                status=400,
            )

        msg_type = data.get('type')
        if msg_type not in ('ping',):
            return JsonResponse({
                'id': msg_id,
                'type': 'Error',
                'params': {
                    'name': 'Bad message type',
                    'message': f'{msg_type} not recognized',
                },
            })

        if data.get('params') is None:
            return JsonResponse({
                'id': msg_id,
                'type': 'Error',
                'params': {
                    'name': 'Bad format',
                    'message': '"params" key not found',
                },
            })

        handler = getattr(self, f'recv_{msg_type}', None)
        if handler:
            return handler(data, client)

        return JsonResponse({
            'id': msg_id,
            'type': 'Error',
            'params': {'name': 'Not implemented',
                       'message': f'{msg_type} not implemented'},
        })

    def recv_ping(self, data, client):
        return JsonResponse({'id': data['id'], 'type': 'pong'})

@method_decorator(csrf_exempt, name='dispatch')
class PollReceiveView(View):
    '''
    GET /ddp/poll/ — drains the Redis message queue for a poll client.

    Returns all pending DDP messages in the format the JS client
    expects: {messages: [{type: 'DDP', params: {...}}, ...]}.
    '''

    def get(self, request):
        client = _get_client(request)
        if not client:
            return JsonResponse(
                {'type': 'Error', 'params': {'name': 'Unauthorized',
                 'message': 'Invalid or missing token'}},
                status=401,
            )

        messages = drain_messages(client.token)
        return JsonResponse({'messages': messages})


@method_decorator(csrf_exempt, name='dispatch')
class TransportSwitchView(View):
    '''
    POST /ddp/switch/ — updates the client's transport to 'poll'.

    Called by the JS client when it detects WebSocket failure and
    falls back to HTTP polling.
    '''

    def post(self, request):
        client = _get_client(request)
        if not client:
            return JsonResponse(
                {'type': 'Error', 'params': {'name': 'Unauthorized',
                 'message': 'Invalid or missing token'}},
                status=401,
            )

        client.transport = 'poll'
        client.save()
        return JsonResponse({'status': 'ok', 'transport': 'poll'})
