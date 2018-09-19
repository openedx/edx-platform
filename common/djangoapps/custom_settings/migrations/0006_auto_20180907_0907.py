# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_settings', '0005_auto_20180907_0635'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customsettings',
            name='course_short_id',
            field=models.IntegerField(unique=True),
        ),
    ]
