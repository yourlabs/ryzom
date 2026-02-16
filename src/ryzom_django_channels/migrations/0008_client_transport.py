from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ryzom_django_channels', '0007_auto_20230327_1510'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='transport',
            field=models.CharField(
                choices=[('ws', 'WebSocket'), ('poll', 'HTTP Polling')],
                default='ws',
                max_length=4,
            ),
        ),
    ]
