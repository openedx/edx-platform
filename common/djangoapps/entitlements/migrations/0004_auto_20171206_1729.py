# -*- coding: utf-8 -*-


import uuid

from django.db import migrations, models


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
