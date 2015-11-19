# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseSoftware',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('full_name', models.CharField(max_length=255)),
                ('url', models.CharField(max_length=255)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='UserLicense',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('serial', models.CharField(max_length=255)),
                ('software', models.ForeignKey(to='licenses.CourseSoftware')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
    ]
