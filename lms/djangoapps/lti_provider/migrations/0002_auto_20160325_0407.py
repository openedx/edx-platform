# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import provider.utils


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
