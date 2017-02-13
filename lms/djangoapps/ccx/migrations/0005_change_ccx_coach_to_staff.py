# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

from django.contrib.auth.models import User
from django.db import migrations
from django.http import Http404

from ccx_keys.locator import CCXLocator
from courseware.courses import get_course_by_id
from instructor.access import allow_access, revoke_access


log = logging.getLogger("edx.ccx")

def change_existing_ccx_coaches_to_staff(apps, schema_editor):
    """
    Modify all coaches of CCX courses so that they have the staff role on the
    CCX course they coach, but retain the CCX Coach role on the parent course.

    Arguments:
        apps (Applications): Apps in edX platform.
        schema_editor (SchemaEditor): For editing database schema (unused)

    """
    CustomCourseForEdX = apps.get_model('ccx', 'CustomCourseForEdX')
    db_alias = schema_editor.connection.alias
    if not db_alias == 'default':
        # This migration is not intended to run against the student_module_history database and
        # will fail if it does. Ensure that it'll only run against the default database.
        return
    list_ccx = CustomCourseForEdX.objects.using(db_alias).all()
    for ccx in list_ccx:
        ccx_locator = CCXLocator.from_course_locator(ccx.course_id, unicode(ccx.id))
        try:
            course = get_course_by_id(ccx_locator)
        except Http404:
            log.error('Could not migrate access for CCX course: %s', unicode(ccx_locator))
        else:
            coach = User.objects.get(id=ccx.coach.id)
            allow_access(course, coach, 'staff', send_email=False)
            revoke_access(course, coach, 'ccx_coach', send_email=False)
            log.info(
                'The CCX coach of CCX %s has been switched from "CCX Coach" to "Staff".',
                unicode(ccx_locator)
            )

def revert_ccx_staff_to_coaches(apps, schema_editor):
    """
    Modify all staff on CCX courses so that they no longer have the staff role
    on the course that they coach.

    Arguments:
        apps (Applications): Apps in edX platform.
        schema_editor (SchemaEditor): For editing database schema (unused)

    """
    CustomCourseForEdX = apps.get_model('ccx', 'CustomCourseForEdX')
    db_alias = schema_editor.connection.alias
    if not db_alias == 'default':
        return
    list_ccx = CustomCourseForEdX.objects.using(db_alias).all()
    for ccx in list_ccx:
        ccx_locator = CCXLocator.from_course_locator(ccx.course_id, unicode(ccx.id))
        try:
            course = get_course_by_id(ccx_locator)
        except Http404:
            log.error('Could not migrate access for CCX course: %s', unicode(ccx_locator))
        else:
            coach = User.objects.get(id=ccx.coach.id)
            allow_access(course, coach, 'ccx_coach', send_email=False)
            revoke_access(course, coach, 'staff', send_email=False)
            log.info(
                'The CCX coach of CCX %s has been switched from "Staff" to "CCX Coach".',
                unicode(ccx_locator)
            )

class Migration(migrations.Migration):

    dependencies = [
        ('ccx', '0001_initial'),
        ('ccx', '0002_customcourseforedx_structure_json'),
        ('ccx', '0003_add_master_course_staff_in_ccx'),
        ('ccx', '0004_seed_forum_roles_in_ccx_courses'),
    ]

    operations = [
        migrations.RunPython(
            code=change_existing_ccx_coaches_to_staff,
            reverse_code=revert_ccx_staff_to_coaches
        )
    ]
