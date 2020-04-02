from django.contrib import admin

# Register your models here.


class RyzomAdminSite(admin.AdminSite):
    site_header = 'Records Department'
    site_title = 'ryzom_dm2'
