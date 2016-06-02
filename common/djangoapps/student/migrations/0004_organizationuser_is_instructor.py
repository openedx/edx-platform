# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0003_auto_20160520_0459'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationuser',
            name='is_instructor',
            field=models.BooleanField(default=False),
        ),
    ]
