# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0006_programsapiconfig_xseries_ad_enabled'),
    ]

    operations = [
        migrations.AlterField(
            model_name='programsapiconfig',
            name='xseries_ad_enabled',
            field=models.BooleanField(default=False, verbose_name='Do we want to show xseries program advertising'),
        ),
    ]
