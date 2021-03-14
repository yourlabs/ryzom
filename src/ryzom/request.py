from channels.http import AsgiRequest


class Request:
    def __init__(self, asgi_request, client, view):
        self.client = client
        self.view = view
        self.__dict__.update(asgi_request.__dict__)
        self.POST = asgi_request.POST
        self.GET = asgi_request.GET
        self.request = asgi_request
