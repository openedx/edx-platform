# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('entitlements', '0002_auto_20171102_0719'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseentitlement',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
    ]
