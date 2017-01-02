# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0010_auto_20160329_2317'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseoverview',
            name='instructor_info',
            field=jsonfield.fields.JSONField(default={}),
            preserve_default=False,
        ),
    ]
