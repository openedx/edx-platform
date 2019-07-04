# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nodebb', '0003_auto_20180312_1021'),
    ]

    operations = [
        migrations.AddField(
            model_name='teamgroupchat',
            name='slug',
            field=models.CharField(default=b'', max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='teamgroupchat',
            name='room_id',
            field=models.IntegerField(),
        ),
    ]
