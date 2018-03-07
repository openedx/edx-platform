# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entitlements', '0006_courseentitlementsupportdetail_action'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='courseentitlementsupportdetail',
            name='reason',
        ),
    ]
