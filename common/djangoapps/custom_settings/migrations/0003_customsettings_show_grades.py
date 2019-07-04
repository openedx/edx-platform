# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_settings', '0002_customsettings_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='customsettings',
            name='show_grades',
            field=models.BooleanField(default=True),
        ),
    ]
