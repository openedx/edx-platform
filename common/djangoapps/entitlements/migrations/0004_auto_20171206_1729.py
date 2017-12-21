# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('entitlements', '0003_auto_20171205_1431'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseentitlement',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
    ]
