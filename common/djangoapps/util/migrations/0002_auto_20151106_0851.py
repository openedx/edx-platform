# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forwards(apps, schema_editor):
    """Ensure that rate limiting is enabled by default. """
    rate_limit_configuration_model = apps.get_model("util", "RateLimitConfiguration")
    db_alias = schema_editor.connection.alias
    rate_limit_configuration_model.objects.using(db_alias).get_or_create(enabled=True)

class Migration(migrations.Migration):

    dependencies = [
        ('util', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards)
    ]
