# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0003_coursepersistentgradesflag_persistentgradesenabledflag'),
    ]

    operations = [
        migrations.AddField(
            model_name='visibleblocks',
            name='course_id',
            field=CourseKeyField(default=CourseKey.from_string('edX/BerylMonkeys/TNL-5458'), max_length=255, db_index=True),
            preserve_default=False,
        ),
    ]
