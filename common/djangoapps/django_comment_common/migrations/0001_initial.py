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
            name='Permission',
            fields=[
                ('name', models.CharField(max_length=30, serialize=False, primary_key=True)),
            ],
            options={
                'db_table': 'django_comment_client_permission',
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('course_id', xmodule_django.models.CourseKeyField(db_index=True, max_length=255, blank=True)),
                ('users', models.ManyToManyField(related_name='roles', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'django_comment_client_role',
            },
        ),
        migrations.AddField(
            model_name='permission',
            name='roles',
            field=models.ManyToManyField(related_name='permissions', to='django_comment_common.Role'),
        ),
    ]
