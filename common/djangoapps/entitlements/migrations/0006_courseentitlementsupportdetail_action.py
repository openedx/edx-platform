# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entitlements', '0005_courseentitlementsupportdetail'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseentitlementsupportdetail',
            name='action',
            field=models.CharField(default='CREATE', max_length=15, choices=[(b'REISSUE', b'Re-issue entitlement'), (b'CREATE', b'Create new entitlement')]),
            preserve_default=False,
        ),
    ]
