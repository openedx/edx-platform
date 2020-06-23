# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations

from cms.djangoapps.contentstore.config.waffle import ENABLE_CHECKLISTS_QUALITY


def create_flag(apps, schema_editor):
    Flag = apps.get_model('waffle', 'Flag')
    # Replacement for flag_undefined_default=True on flag definition
    Flag.objects.get_or_create(name=ENABLE_CHECKLISTS_QUALITY.namespaced_flag_name, defaults={'everyone': True})


class Migration(migrations.Migration):
    dependencies = [
        ('contentstore', '0004_remove_push_notification_configmodel_table'),
        ('waffle', '0001_initial'),
    ]

    operations = [
        # Do not remove the flag for rollback.  We don't want to lose original if
        # it already existed, and it won't hurt if it was created.
        migrations.RunPython(create_flag, reverse_code=migrations.RunPython.noop),
    ]
