# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ccx_keys.locator import CCXLocator
from django.db import migrations

from lms.djangoapps.ccx.models import CustomCourseForEdX
from lms.djangoapps.ccx.utils import (
    add_master_course_staff_to_ccx,
    reverse_add_master_course_staff_to_ccx
)


def add_master_course_staff_to_ccx_for_existing_ccx(apps, schema_editor):
    """
    Add all staff and admin of master course to respective CCX(s).
    """
    list_ccx = CustomCourseForEdX.objects.all()
    for ccx in list_ccx:
        ccx_locator = CCXLocator.from_course_locator(ccx.course_id, unicode(ccx.id))
        add_master_course_staff_to_ccx(ccx.course, ccx_locator, ccx.display_name)


def reverse_add_master_course_staff_to_ccx_for_existing_ccx(apps, schema_editor):
    """
    Add all staff and admin of master course to respective CCX(s).
    """
    list_ccx = CustomCourseForEdX.objects.all()
    for ccx in list_ccx:
        ccx_locator = CCXLocator.from_course_locator(ccx.course_id, unicode(ccx.id))
        reverse_add_master_course_staff_to_ccx(ccx.course, ccx_locator, ccx.display_name)


class Migration(migrations.Migration):

    dependencies = [
        ('ccx', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            add_master_course_staff_to_ccx_for_existing_ccx,
            reverse_code=reverse_add_master_course_staff_to_ccx_for_existing_ccx
        )
    ]
