# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0004_visibleblocks_course_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursepersistentgradesflag',
            name='course_id',
            field=CourseKeyField(max_length=255, db_index=True),
        ),
    ]
