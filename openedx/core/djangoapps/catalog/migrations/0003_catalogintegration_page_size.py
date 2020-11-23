# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_catalogintegration_username'),
    ]

    operations = [
        migrations.AddField(
            model_name='catalogintegration',
            name='page_size',
            field=models.PositiveIntegerField(default=100, help_text='Maximum number of records in paginated response of a single request to catalog service.', verbose_name='Page Size'),
        ),
    ]
