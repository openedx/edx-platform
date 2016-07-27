# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('course_groups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CohortMembership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255)),
            ],
        ),

        migrations.AddField(
            model_name='cohortmembership',
            name='course_user_group',
            field=models.ForeignKey(to='course_groups.CourseUserGroup'),
        ),
        migrations.AddField(
            model_name='cohortmembership',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='cohortmembership',
            unique_together=set([('user', 'course_id')]),
        ),
    ]
