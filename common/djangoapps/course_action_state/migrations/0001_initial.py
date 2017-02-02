# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseRerunState',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('updated_time', models.DateTimeField(auto_now=True)),
                ('course_key', CourseKeyField(max_length=255, db_index=True)),
                ('action', models.CharField(max_length=100, db_index=True)),
                ('state', models.CharField(max_length=50)),
                ('should_display', models.BooleanField(default=False)),
                ('message', models.CharField(max_length=1000)),
                ('source_course_key', CourseKeyField(max_length=255, db_index=True)),
                ('display_name', models.CharField(default=b'', max_length=255, blank=True)),
                ('created_user', models.ForeignKey(related_name='created_by_user+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
                ('updated_user', models.ForeignKey(related_name='updated_by_user+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='coursererunstate',
            unique_together=set([('course_key', 'action')]),
        ),
    ]
