import importlib
import sys

from django import http
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views import generic
from django.urls import include, path, reverse_lazy

from ryzom import bundle
from ryzom import html


class CSSBundle(html.Stylesheet):
    def to_html(self, *content, **context):
        if settings.DEBUG:
            self.attrs.href = reverse_lazy('bundle_css')
        else:
            self.attrs.href = staticfiles_storage.url('bundle.css')
        return super().to_html(*content, **context)


class JSBundle(html.Script):
    def to_html(self, *content, **context):
        if settings.DEBUG:
            self.attrs.src = reverse_lazy('bundle_js')
        else:
            self.attrs.src = staticfiles_storage.url('bundle.js')
        return super().to_html(*content, **context)


def get_component_modules():
    names = []
    for app in settings.INSTALLED_APPS:
        for subname in ('views', 'urls', 'components', 'html'):
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
