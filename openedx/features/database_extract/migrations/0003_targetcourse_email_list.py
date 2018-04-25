# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database_extract', '0002_auto_20180329_0553'),
    ]

    operations = [
        migrations.AddField(
            model_name='targetcourse',
            name='email_list',
            field=models.TextField(default='osama.arshad@arbisoft.com'),
            preserve_default=False,
        ),
    ]
