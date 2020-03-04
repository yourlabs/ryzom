from django import forms
from django.conf import settings
from django.urls import reverse_lazy
from django.views import generic

from .models import Record
from django.utils.datetime_safe import date

# Create your views here.


class RecordModelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # When creating a record, force the field labels to float above any
        # date fields.
        if not self.is_bound:
            for k, f in self.fields.items():
                if isinstance(f.widget, forms.DateInput):
                    f.initial = date.today()

    class Meta:
        model = Record
        fields = '__all__'
        widgets = {
            'date_field': forms.DateInput(
                attrs={'type': 'date'},
                format=settings.DATE_INPUT_FORMATS[0],
            ),
            'choice_radio_field': forms.RadioSelect(),
        }


class RecordIndex(generic.ListView):
    queryset = Record.objects.all()


class RecordDetail(generic.DetailView):
    model = Record


class RecordCreate(generic.CreateView):
    model = Record
    form_class = RecordModelForm


class RecordUpdate(generic.UpdateView):
    model = Record
    form_class = RecordModelForm


class RecordDelete(generic.DeleteView):
    model = Record
    succes_url = reverse_lazy('records:detail')
