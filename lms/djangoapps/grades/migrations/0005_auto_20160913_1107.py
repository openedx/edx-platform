# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0004_visibleblocks_course_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='visibleblocks',
            name='course_id',
            field=xmodule_django.models.CourseKeyField(max_length=255, db_index=True),
        ),
    ]
