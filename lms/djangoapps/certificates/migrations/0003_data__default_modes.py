# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Converted from the original South migration 0002_default_rate_limit_config.py

from django.db import migrations, models
from django.conf import settings
from django.core.files import File

def forwards(apps, schema_editor):
    """Add default modes"""
    BadgeImageConfiguration = apps.get_model("certificates", "BadgeImageConfiguration")

    objects = BadgeImageConfiguration.objects
    if not objects.exists():
        for mode in ['honor', 'verified', 'professional']:
            conf = objects.create(mode=mode)
            file_name = '{0}{1}'.format(mode, '.png')
            conf.icon.save(
                'badges/{}'.format(file_name),
                File(open(settings.PROJECT_ROOT / 'static' / 'images' / 'default-badges' / file_name))
            )

            conf.save()

def backwards(apps, schema_editor):
    """Do nothing, assumptions too dangerous."""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0002_data__certificatehtmlviewconfiguration_data'),
    ]

    operations = [
        migrations.RunPython(forwards,backwards)
    ]
