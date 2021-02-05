from django.utils.translation import gettext_lazy as _

from crudlfap import shortcuts as crudlfap


class Home(crudlfap.TemplateView):
    template_name = 'crudlfap/home.html'
    urlname = 'home'
    urlpath = ''
    title = _('Home')
    title_heading = ''
    material_icon = 'home'
    authenticate = False
