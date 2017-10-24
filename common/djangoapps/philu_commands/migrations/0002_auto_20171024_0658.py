# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('philu_commands', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='FailedUsers',
            new_name='CreationFailedUsers',
        ),
    ]
