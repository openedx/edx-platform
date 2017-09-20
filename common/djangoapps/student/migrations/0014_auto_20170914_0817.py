# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0013_userprofile_is_poc'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='is_poc',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='organization',
        ),
        migrations.DeleteModel(
            name='Organization',
        ),
    ]
