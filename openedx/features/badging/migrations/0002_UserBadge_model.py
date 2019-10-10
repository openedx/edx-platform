# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import openedx.core.djangoapps.xmodule_django.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('badging', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserBadge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255, db_column=b'course_id', db_index=True)),
                ('community_id', models.IntegerField(db_column=b'community_id')),
                ('date_earned', models.DateTimeField(auto_now=True)),
                ('badge', models.ForeignKey(to='badging.Badge')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='userbadge',
            unique_together=set([('user', 'badge', 'course_id', 'community_id')]),
        ),
    ]
