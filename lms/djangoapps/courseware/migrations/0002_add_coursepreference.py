# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        ('courseware', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoursePreference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('pref_key', models.CharField(max_length=255)),
                ('pref_value', models.CharField(max_length=255, null=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='coursepreference',
            unique_together=set([('course_id', 'pref_key')]),
        ),
    ]
