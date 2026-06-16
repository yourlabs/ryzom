from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ryzom_django_channels', '0009_client_detached_resync'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='last_seen',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
