# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth_dispatch', '0002_auto_20161016_0926'),
    ]

    operations = [
        migrations.AddField(
            model_name='restrictedapplication',
            name='_allowed_users',
            field=models.TextField(null=True, blank=True),
        ),
    ]
