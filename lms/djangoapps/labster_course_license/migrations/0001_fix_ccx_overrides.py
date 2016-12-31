# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forwards(apps, schema_editor):
    """
    Removes all field overrides for `visible_to_staff_only=False` field (visible for all).
    In this case, the value from Master course is taken.

    It solves the issue when the block becomes hidden in Master Course, but is still
    displayed in CCX that causes Permission Denied error in ModuleRender system (access is
    restricted in Master Course).

    This migration solves the issue for old courses. On the way to avoid similar
    problem in future, additional changes have been added in:
     * lms/djangoapps/labster_course_license/views.py:98
     * lms/djangoapps/ccx/views.py:267-270
    """
    CcxFieldOverride = apps.get_model("ccx", "CcxFieldOverride")

    qs = CcxFieldOverride.objects.filter(
        field="visible_to_staff_only", value=False
    )
    count = qs.count()
    qs.delete()
    print "%d fields has been removed.s" % count


class Migration(migrations.Migration):

    dependencies = [
        ('ccx', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop)
    ]
