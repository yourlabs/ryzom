

class UnpolyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Up-Location'] = request.path_info + '?' + request.GET.urlencode()
        return response
