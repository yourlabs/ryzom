from django.middleware.csrf import get_token

from ryzom_mdc import *
from ryzom_django import html as ryzom_django


class Html(ryzom_django.Html, Html):
    pass


class CSRFInput(Input):
    def __init__(self, request):
        super().__init__(
            type='hidden',
            name='csrfmiddlewaretoken',
            value=get_token(request)
        )
