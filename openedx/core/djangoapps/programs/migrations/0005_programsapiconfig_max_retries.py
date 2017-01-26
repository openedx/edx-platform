# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0004_programsapiconfig_enable_certification'),
    ]

    operations = [
        migrations.AddField(
            model_name='programsapiconfig',
            name='max_retries',
            field=models.PositiveIntegerField(default=11, help_text='When making requests to award certificates, make at most this many attempts to retry a failing request.', verbose_name='Maximum Certification Retries'),
        ),
    ]
