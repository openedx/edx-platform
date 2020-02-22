# -*- coding: utf-8 -*-


import logging

import six
from ccx_keys.locator import CCXLocator
from django.db import migrations
from django.http import Http404

from lms.djangoapps.courseware.courses import get_course_by_id
from lms.djangoapps.ccx.utils import add_master_course_staff_to_ccx, remove_master_course_staff_from_ccx

log = logging.getLogger("edx.ccx")


def add_master_course_staff_to_ccx_for_existing_ccx(apps, schema_editor):
    """
    Add all staff and admin of master course to respective CCX(s).

    Arguments:
        apps (Applications): Apps in edX platform.
        schema_editor (SchemaEditor): For editing database schema i.e create, delete field (column)

    """
    CustomCourseForEdX = apps.get_model("ccx", "CustomCourseForEdX")
    list_ccx = CustomCourseForEdX.objects.all()
    for ccx in list_ccx:
        if not ccx.course_id or ccx.course_id.deprecated:
            # prevent migration for deprecated course ids or invalid ids.
            continue
        ccx_locator = CCXLocator.from_course_locator(ccx.course_id, six.text_type(ccx.id))
        try:
            course = get_course_by_id(ccx.course_id)
            add_master_course_staff_to_ccx(
                course,
                ccx_locator,
                ccx.display_name,
                send_email=False
            )
        except Http404:
            log.warning(
                "Unable to add instructors and staff of master course %s to ccx %s.",
                ccx.course_id,
                ccx_locator
            )


def remove_master_course_staff_from_ccx_for_existing_ccx(apps, schema_editor):
    """
    Remove all staff and instructors of master course from respective CCX(s).

    Arguments:
        apps (Applications): Apps in edX platform.
        schema_editor (SchemaEditor): For editing database schema i.e create, delete field (column)

    """
    CustomCourseForEdX = apps.get_model("ccx", "CustomCourseForEdX")
    list_ccx = CustomCourseForEdX.objects.all()
    for ccx in list_ccx:
        if not ccx.course_id or ccx.course_id.deprecated:
            # prevent migration for deprecated course ids or invalid ids.
            continue
        ccx_locator = CCXLocator.from_course_locator(ccx.course_id, six.text_type(ccx.id))
        try:
            course = get_course_by_id(ccx.course_id)
            remove_master_course_staff_from_ccx(
                course,
                ccx_locator,
                ccx.display_name,
                send_email=False
            )
        except Http404:
            log.warning(
                "Unable to remove instructors and staff of master course %s from ccx %s.",
                ccx.course_id,
                ccx_locator
            )

class Migration(migrations.Migration):

    dependencies = [
        ('ccx', '0001_initial'),
        ('ccx', '0002_customcourseforedx_structure_json'),
        ('course_overviews','0010_auto_20160329_2317'), # because we use course overview and are in the same release as that table is modified
        ('verified_track_content','0001_initial'), # because we use enrollement code and are in the same release as an enrollement related table is created
    ]

    operations = [
        migrations.RunPython(
            code=add_master_course_staff_to_ccx_for_existing_ccx,
            reverse_code=remove_master_course_staff_from_ccx_for_existing_ccx
        )
    ]
