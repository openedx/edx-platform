# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import openedx.core.djangoapps.xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0013_courseoverview_language'),
        ('course_modes', '0007_coursemode_bulk_sku'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursemode',
            name='course_id',
            field=openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255, db_index=True, verbose_name="Course", db_column='course_id'),
        ),
        migrations.RenameField(
            model_name='coursemode',
            old_name='course_id',
            new_name='course',
        ),
        migrations.AlterField(
            model_name='coursemode',
            name='course',
            field=models.ForeignKey(related_name='modes', db_constraint=False, default=None, to='course_overviews.CourseOverview'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='coursemode',
            unique_together=set([('course', 'mode_slug', 'currency')]),
        ),
    ]
