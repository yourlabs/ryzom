from django import forms
from django.contrib import admin
from django.db import models
from django.forms.widgets import RadioSelect

from .models import Record

# Register your models here.


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ('char_field', 'date_field')
    radio_fields = {'choice_radio_field': admin.VERTICAL}
