# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nodebb', '0002_teamgroupchat'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discussioncommunity',
            name='community_url',
            field=models.CharField(unique=True, max_length=255),
        ),
    ]
