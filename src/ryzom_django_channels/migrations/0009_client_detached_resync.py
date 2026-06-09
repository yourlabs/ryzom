from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ryzom_django_channels', '0008_client_transport'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='detached_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='needs_resync',
            field=models.BooleanField(default=False),
        ),
    ]
