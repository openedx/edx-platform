# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField, LocationKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CcxFieldOverride',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('location', LocationKeyField(max_length=255, db_index=True)),
                ('field', models.CharField(max_length=255)),
                ('value', models.TextField(default=b'null')),
            ],
        ),
        migrations.CreateModel(
            name='CustomCourseForEdX',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('display_name', models.CharField(max_length=255)),
                ('coach', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='ccxfieldoverride',
            name='ccx',
            field=models.ForeignKey(to='ccx.CustomCourseForEdX'),
        ),
        migrations.AlterUniqueTogether(
            name='ccxfieldoverride',
            unique_together=set([('ccx', 'location', 'field')]),
        ),
    ]
