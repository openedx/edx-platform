# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_settings', '0008_customsettings_seo_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='customsettings',
            name='auto_enroll',
            field=models.BooleanField(default=False),
        ),
    ]
