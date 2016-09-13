# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0003_coursepersistentgradesflag_persistentgradesenabledflag'),
    ]

    operations = [
        migrations.AddField(
            model_name='visibleblocks',
            name='course_id',
            field=xmodule_django.models.CourseKeyField(default=b'', max_length=255, db_index=True),
        ),
    ]
