import importlib

from django.conf import settings

from ryzom.request import Request


class RyzomMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        request.ryzom = None
        if getattr(settings, 'DDP_URLPATTERNS', None):
            urls = importlib.import_module(settings.DDP_URLPATTERNS).urlpatterns
            url = request.path_info.lstrip('/')
            for u in urls:
                if u.pattern.match(url):
                    request.ryzom_view = u.callback
                    break

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
