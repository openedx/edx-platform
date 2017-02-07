# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0009_auto_20170111_0422'),
    ]

    operations = [
        migrations.RunSQL(
            "create unique index email on auth_user (email);",
            "drop index email on auth_user;",
        )
    ]

