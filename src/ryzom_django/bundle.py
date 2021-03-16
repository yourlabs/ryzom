import importlib

from django import http
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views import generic
from django.urls import include, path, reverse

from ryzom import bundle
from ryzom import html


class CSSBundle(html.Style):
    def __init__(self, **attrs):
        if settings.DEBUG:
            attrs['href'] = reverse('bundle_css')
        else:
            attrs['href'] = staticfiles_storage.url('bundle.css')
        super().__init__(**attrs)


class JSBundle(html.Script):
    def __init__(self, **attrs):
        if settings.DEBUG:
            attrs['src'] = reverse('bundle_js')
        else:
            attrs['src'] = staticfiles_storage.url('bundle.js')
        super().__init__(**attrs)


def get_component_modules():
    names = []
    for app in settings.INSTALLED_APPS:
        for subname in ('views', 'urls', 'components'):
            name = '.'.join([app, subname])
            try:
                importlib.import_module(name)
            except ImportError:
                continue
            names.append(name)
    return names


def js():
    return bundle.js(*get_component_modules())


def css():
    return bundle.css(*get_component_modules())


class CSSBundleView(generic.View):
    def get(self, *args, **kwargs):
        response = http.HttpResponse(css())
        response['Content-Type'] = 'text/css'
        return response

    @classmethod
    def as_url(cls):
        return path('bundle.css', cls.as_view(), name='bundle_css')


class JSBundleView(generic.View):
    def get(self, *args, **kwargs):
        response = http.HttpResponse(js())
        response['Content-Type'] = 'text/javascript'
        return response

    @classmethod
    def as_url(cls):
        return path('bundle.js', cls.as_view(), name='bundle_js')


urlpatterns = [
    JSBundleView.as_url(),
    CSSBundleView.as_url(),
]
