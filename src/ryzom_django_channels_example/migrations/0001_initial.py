# Generated by Django 3.1.4 on 2021-03-14 20:05

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import ryzom_django_channels.pubsub


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
            bases=(ryzom_django_channels.pubsub.Publishable, models.Model),
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=1024)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ryzom_django_channels_example.room')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            bases=(ryzom_django_channels.pubsub.Publishable, models.Model),
        ),
    ]
