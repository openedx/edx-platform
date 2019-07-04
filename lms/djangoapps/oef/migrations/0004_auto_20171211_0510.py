# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('oef', '0003_organizationoefscore'),
    ]

    operations = [
        migrations.AddField(
            model_name='option',
            name='short_text',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
