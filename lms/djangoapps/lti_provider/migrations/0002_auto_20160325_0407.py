# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import provider.utils
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lti_provider', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lticonsumer',
            name='consumer_secret',
            field=models.CharField(default=provider.utils.short_token, unique=True, max_length=32),
        ),
    ]
