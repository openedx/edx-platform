# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_settings', '0006_auto_20180907_0907'),
    ]

    operations = [
        migrations.AddField(
            model_name='customsettings',
            name='enable_enrollment_email',
            field=models.BooleanField(default=True),
        ),
    ]
