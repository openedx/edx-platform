# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0007_programsapiconfig_program_listing_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='programsapiconfig',
            name='program_details_enabled',
            field=models.BooleanField(default=False, verbose_name='Do we want to show program details pages'),
        ),
    ]
