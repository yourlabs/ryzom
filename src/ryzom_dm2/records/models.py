from django.conf import settings
from django.db import models
from django.template import engines  # , Template
from django.template.defaultfilters import date
from django.urls import reverse

# Create your models here.


class Record(models.Model):
    VINYL = 'vinyl'
    CD = 'cd'
    MP3 = 'mp3'
    VHS = 'vhs'
    DVD = 'dvd'
    BLURAY = 'blu-ray'
    MEDIA_CHOICES = (
        ('Audio', (
            (VINYL, 'Vinyl'),
            (CD, 'CD'),
            (MP3, 'MP3')
            )
         ),
        ('Video', (
            (VHS, 'VHS tape'),
            (DVD, 'DVD'),
            (BLURAY, 'Blu-ray')
            )
         ),
    )

    char_field = models.CharField('Char field', max_length=50)
    date_field = models.DateField('Date field')
    email_field = models.EmailField('Email field')
    boolean_field = models.BooleanField()
    null_boolean_field = models.NullBooleanField()
    choice_field = models.CharField('Choice field',
                                    max_length=50,
                                    choices=MEDIA_CHOICES)
    # choice_radio_field to be overridden in forms: widget=models.RadioSelect()
    choice_radio_field = models.CharField('Choice Radio field',
                                          max_length=50,
                                          choices=MEDIA_CHOICES)

    def __str__(self):
        result = ": ".join([
            self.char_field,
            date(self.date_field, 'SHORT_DATE_FORMAT')
        ])
        return result

    def get_absolute_url(self):
        return reverse('records:detail', kwargs={'pk': self.pk})
