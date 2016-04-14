# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='VerifiedTrackCohortedCourse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_key', xmodule_django.models.CourseKeyField(help_text='The course key for the course we would like to be auto-cohorted.', unique=True, max_length=255, db_index=True)),
                ('enabled', models.BooleanField()),
            ],
        ),
    ]
