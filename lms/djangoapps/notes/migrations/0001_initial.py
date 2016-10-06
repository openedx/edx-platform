# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('uri', models.CharField(max_length=255, db_index=True)),
                ('text', models.TextField(default=b'')),
                ('quote', models.TextField(default=b'')),
                ('range_start', models.CharField(max_length=2048)),
                ('range_start_offset', models.IntegerField()),
                ('range_end', models.CharField(max_length=2048)),
                ('range_end_offset', models.IntegerField()),
                ('tags', models.TextField(default=b'')),
                ('created', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
