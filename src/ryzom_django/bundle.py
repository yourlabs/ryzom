import importlib

from django import http
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views import generic
from django.urls import include, path, reverse_lazy

from ryzom import bundle
from ryzom import html


if settings.DEBUG:
    CSS_BUNDLE_URL = reverse_lazy('bundle_css')
    JS_BUNDLE_URL = reverse_lazy('bundle_js')
else:
    CSS_BUNDLE_URL = staticfiles_storage.url('bundle.css')
    JS_BUNDLE_URL = staticfiles_storage.url('bundle.js')


class CSSBundle(html.Stylesheet):
    attrs = dict(href=CSS_BUNDLE_URL)


class JSBundle(html.Script):
    attrs = dict(src=JS_BUNDLE_URL)


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
