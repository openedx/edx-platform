# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseteam',
            name='discussion_topic_id',
            field=models.CharField(default=0, unique=True, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='courseteam',
            name='last_activity_at',
            field=models.DateTimeField(default=datetime.datetime(2016, 9, 15, 6, 54, 3, 634153, tzinfo=utc), db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='courseteam',
            name='team_size',
            field=models.IntegerField(default=0, db_index=True),
        ),
        migrations.RemoveField(
            model_name='courseteam',
            name='is_active',
        ),
        migrations.AddField(
            model_name='courseteammembership',
            name='last_activity_at',
            field=models.DateTimeField(default=datetime.datetime(2016, 9, 15, 6, 54, 25, 218360, tzinfo=utc)),
            preserve_default=False,
        ),
    ]
