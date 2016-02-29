# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ccx_keys.locator import CCXLocator
from courseware.courses import get_course_by_id
from contextlib import contextmanager
from django.db import migrations

from lms.djangoapps.instructor.enrollment import (
    enroll_email,
    get_email_params,
    unenroll_email,
)
from lms.djangoapps.instructor.access import (
    allow_access,
    list_with_level,
    revoke_access,
)


@contextmanager
def ccx_course(ccx_locator):
    """Create a context in which the course identified by course_locator exists
    """
    course = get_course_by_id(ccx_locator)
    yield course


def add_master_course_staff_to_ccx_for_existing_ccx(apps, schema_editor):
    """
    Add all staff and admin of master course to respective CCX(s).
    """
    CustomCourseForEdX = apps.get_model("ccx", "CustomCourseForEdX")
    list_ccx = CustomCourseForEdX.objects.all()
    for ccx in list_ccx:
        if ccx.course_id.deprecated:
            # prevent migration for deprecated course ids.
            continue
        ccx_locator = CCXLocator.from_course_locator(ccx.course_id, unicode(ccx.id))
        add_master_course_staff_to_ccx(
            get_course_by_id(ccx.course_id),
            ccx_locator,
            ccx.display_name
        )


def reverse_add_master_course_staff_to_ccx_for_existing_ccx(apps, schema_editor):
    """
    Add all staff and admin of master course to respective CCX(s).
    """
    CustomCourseForEdX = apps.get_model("ccx", "CustomCourseForEdX")
    list_ccx = CustomCourseForEdX.objects.all()
    for ccx in list_ccx:
        if ccx.course_id.deprecated:
            # prevent migration for deprecated course ids.
            continue
        ccx_locator = CCXLocator.from_course_locator(ccx.course_id, unicode(ccx.id))
        reverse_add_master_course_staff_to_ccx(
            get_course_by_id(ccx.course_id),
            ccx_locator
        )


def add_master_course_staff_to_ccx(master_course, ccx_key, display_name, send_email=False):
    """
    Added staff role on ccx to all the staff members of master course.
    Arguments:
        master_course (CourseDescriptorWithMixins): Master course instance
        ccx_key (CCXLocator): CCX course key
        display_name (str): ccx display name for email
    """
    list_staff = list_with_level(master_course, 'staff')
    list_instructor = list_with_level(master_course, 'instructor')

    with ccx_course(ccx_key) as course_ccx:
        email_params = get_email_params(course_ccx, auto_enroll=True, course_key=ccx_key, display_name=display_name)
        list_staff_ccx = list_with_level(course_ccx, 'staff')
        list_instructor_ccx = list_with_level(course_ccx, 'instructor')
        for staff in list_staff:
            # this call should be idempotent
            if staff not in list_staff_ccx:
                # allow 'staff' access on ccx to staff of master course
                allow_access(course_ccx, staff, 'staff')

                # Enroll the staff in the ccx
                enroll_email(
                    course_id=ccx_key,
                    student_email=staff.email,
                    auto_enroll=True,
                    email_students=send_email,
                    email_params=email_params,
                )

        for instructor in list_instructor:
            # this call should be idempotent
            if instructor not in list_instructor_ccx:
                # allow 'instructor' access on ccx to instructor of master course
                allow_access(course_ccx, instructor, 'instructor')

                # Enroll the instructor in the ccx
                enroll_email(
                    course_id=ccx_key,
                    student_email=instructor.email,
                    auto_enroll=True,
                    email_students=send_email,
                    email_params=email_params,
                )


def reverse_add_master_course_staff_to_ccx(master_course, ccx_key, send_email=False):
    """
    Remove staff of ccx.

    Arguments:
        master_course (CourseDescriptorWithMixins): Master course instance
        ccx_key (CCXLocator): CCX course key
        display_name (str): ccx display name for email
    """
    list_staff = list_with_level(master_course, 'staff')
    list_instructor = list_with_level(master_course, 'instructor')

    with ccx_course(ccx_key) as course_ccx:
        email_params = get_email_params(course_ccx, auto_enroll=True, course_key=ccx_key)
        for staff in list_staff:
            # allow 'staff' access on ccx to staff of master course
            revoke_access(course_ccx, staff, 'staff')

            # Enroll the staff in the ccx
            unenroll_email(
                course_id=ccx_key,
                student_email=staff.email,
                email_students=send_email,
                email_params=email_params,
            )

        for instructor in list_instructor:
            # allow 'instructor' access on ccx to instructor of master course
            revoke_access(course_ccx, instructor, 'instructor')

            # Enroll the instructor in the ccx
            unenroll_email(
                course_id=ccx_key,
                student_email=instructor.email,
                email_students=send_email,
                email_params=email_params,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('ccx', '0001_initial'),
        ('ccx', '0002_customcourseforedx_structure_json'),
    ]

    operations = [
        migrations.RunPython(
            code=add_master_course_staff_to_ccx_for_existing_ccx,
            reverse_code=reverse_add_master_course_staff_to_ccx_for_existing_ccx
        )
    ]
