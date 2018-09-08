# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


def add_course_short_id_old_records(apps, schema_editor):
    custom_settings = apps.get_model('custom_settings', "CustomSettings")
    settings = custom_settings.objects.all()

    short_id = 100
    for setting in settings:
        setting.course_short_id = short_id
        short_id += 1
        setting.save()


class Migration(migrations.Migration):

    dependencies = [
        ('custom_settings', '0004_customsettings_course_short_id'),
    ]

    operations = [
        migrations.RunPython(add_course_short_id_old_records),
    ]




