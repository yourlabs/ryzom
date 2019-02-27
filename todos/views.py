import json
from django.shortcuts import render


def index(request, url=''):
    print(json.dumps(request.GET))
    return render(request, 'index.html', {
            'url': url,
            'query_string': request.GET.urlencode()
        })
