# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import openedx.core.djangoapps.xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0013_courseoverview_language'),
        ('student', '0010_auto_20170207_0458'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseenrollment',
            name='course_id',
            field=openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255, db_index=True, db_column='course_id'),
        ),
        migrations.AlterField(
            model_name='historicalcourseenrollment',
            name='course_id',
            field=openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255, db_index=True, db_column='course_id'),
        ),
        migrations.RenameField(
            model_name='courseenrollment',
            old_name='course_id',
            new_name='course',
        ),
        migrations.RenameField(
            model_name='historicalcourseenrollment',
            old_name='course_id',
            new_name='course',
        ),
        migrations.AlterField(
            model_name='courseenrollment',
            name='course',
            field=models.ForeignKey(db_constraint=False, to='course_overviews.CourseOverview'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='historicalcourseenrollment',
            name='course',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='course_overviews.CourseOverview', null=True),
            preserve_default=True,
        ),

        migrations.AlterModelOptions(
            name='courseenrollment',
            options={'ordering': ('user', 'course')},
        ),
        migrations.AlterUniqueTogether(
            name='courseenrollment',
            unique_together=set([('user', 'course')]),
        ),
    ]
