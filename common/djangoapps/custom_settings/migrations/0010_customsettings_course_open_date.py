# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_settings', '0009_customsettings_auto_enroll'),
    ]

    operations = [
        migrations.AddField(
            model_name='customsettings',
            name='course_open_date',
            field=models.DateTimeField(null=True),
        ),
    ]
