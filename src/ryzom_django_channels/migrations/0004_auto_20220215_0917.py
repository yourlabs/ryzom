# Generated by Django 3.2.12 on 2022-02-15 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ryzom_django_channels', '0003_alter_subscription_queryset'),
    ]

    operations = [
        migrations.AddField(
            model_name='registration',
            name='options',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='registration',
            name='subscriber_class',
            field=models.CharField(default='Div', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='registration',
            name='subscriber_module',
            field=models.CharField(default='ryzom.html', max_length=255),
            preserve_default=False,
        ),
    ]
