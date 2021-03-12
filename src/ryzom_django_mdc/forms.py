from django import forms
from ryzom_mdc import MDCErrorList
from ryzom_django.forms import *

forms.BaseForm.non_field_error_component = MDCErrorList
