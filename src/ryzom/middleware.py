import importlib
from django.conf import settings


class RyzomMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        request.ryzom = None
        urls = importlib.import_module(settings.DDP_URLPATTERNS).urlpatterns
        url = request.path_info.lstrip('/')
        for u in urls:
            if u.pattern.match(url):
                request.ryzom = u.callback('')
                request.ryzom.oncreate(url)
                request.ryzom.onurl(url)
                break

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
