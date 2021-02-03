'''
Project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

""" original `project/urls.py`
from django.conf.urls import include, url

urlpatterns = [
    url('^', include('ryzom.urls')),
]
'''
from crudlfap import shortcuts as crudlfap

from django.conf import settings
from django.conf.urls import include, url, re_path
from django.utils.translation import ugettext_lazy as _
from django.views.generic import RedirectView
from django.views.static import serve

from .views import Home


crudlfap.site.title = _('Ryzom - Demo')  # used by base.html
crudlfap.site.urlpath = 'admin'  # example url prefix
crudlfap.site.views['home'] = Home

urlpatterns = [
    crudlfap.site.urlpattern,
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/images/favicon.ico')),
    re_path(
        r'^%s(?P<path>.*)$' % settings.STATIC_URL.lstrip('/'),
        serve,
        kwargs=dict(document_root=settings.STATIC_ROOT)
    ),
    url('', include('ryzom.urls')),
]
if 'debug_toolbar' in settings.INSTALLED_APPS and settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
