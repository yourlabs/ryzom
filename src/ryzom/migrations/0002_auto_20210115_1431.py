# Generated by Django 3.0.10 on 2021-01-15 14:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ryzom', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ryzom.Clients'),
        ),
    ]
