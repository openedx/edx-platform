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
            name='CourseAuthorization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', xmodule_django.models.CourseKeyField(unique=True, max_length=255, db_index=True)),
                ('email_enabled', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='CourseEmail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.CharField(max_length=128, db_index=True)),
                ('subject', models.CharField(max_length=128, blank=True)),
                ('html_message', models.TextField(null=True, blank=True)),
                ('text_message', models.TextField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('to_option', models.CharField(default=b'myself', max_length=64, choices=[(b'myself', b'Myself'), (b'staff', b'Staff and instructors'), (b'all', b'All')])),
                ('template_name', models.CharField(max_length=255, null=True)),
                ('from_addr', models.CharField(max_length=255, null=True)),
                ('sender', models.ForeignKey(default=1, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CourseEmailTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('html_template', models.TextField(null=True, blank=True)),
                ('plain_template', models.TextField(null=True, blank=True)),
                ('name', models.CharField(max_length=255, unique=True, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Optout',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='optout',
            unique_together=set([('user', 'course_id')]),
        ),
    ]
