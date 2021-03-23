from django import forms

from ryzom_django.forms import *
from ryzom_mdc.html import MDCErrorList

forms.BaseForm.non_field_error_component = MDCErrorList
