# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0012_userprofile_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='is_poc',
            field=models.BooleanField(default=False),
        ),
    ]
