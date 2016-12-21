# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_catalogintegration_username'),
    ]

    operations = [
        migrations.AddField(
            model_name='catalogintegration',
            name='course_run_cache_ttl',
            field=models.PositiveIntegerField(default=0, help_text='Specified in seconds. Enable caching of Course Run API response by setting this to a value greater than 0.', verbose_name='Cache Time To Live for Course Run Data'),
        ),
    ]
