"""
Instructor Dashboard Views

TODO add tracking
"""

import csv
import json
import logging
import os
import re
import requests
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from mitxmako.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.utils.html import escape
from django.http import Http404

from django.conf import settings
from courseware.access import has_access, get_access_group_name, course_beta_test_group_name
from courseware.courses import get_course_by_id
from django_comment_client.utils import has_forum_access
from instructor.offline_gradecalc import student_grades, offline_grades_available
from django_comment_common.models import Role, FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA
from xmodule.modulestore.django import modulestore
from student.models import CourseEnrollment


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def instructor_dashboard_2(request, course_id):
    """Display the instructor dashboard for a course."""

    course = get_course_by_id(course_id, depth=None)
    instructor_access = has_access(request.user, course, 'instructor')   # an instructor can manage staff lists
    staff_access = has_access(request.user, course, 'staff')
    forum_admin_access = has_forum_access(request.user, course_id, FORUM_ROLE_ADMINISTRATOR)

    if not staff_access:
        raise Http404

    sections = [
        _section_course_info(course_id),
        _section_membership(course_id),
        _section_student_admin(course_id),
        _section_data_download(course_id),
        _section_analytics(course_id),
    ]

    context = {
        'course': course,
        'staff_access': True,
        'admin_access': request.user.is_staff,
        'instructor_access': instructor_access,
        'forum_admin_access': forum_admin_access,
        'djangopid': os.getpid(),
        'mitx_version': getattr(settings, 'MITX_VERSION_STRING', ''),
        'cohorts_ajax_url': reverse('cohorts', kwargs={'course_id': course_id}),
        'old_dashboard_url': reverse('instructor_dashboard', kwargs={'course_id': course_id}),
        'sections': sections
    }

    return render_to_response('courseware/instructor_dashboard_2/instructor_dashboard_2.html', context)


"""
Section functions starting with _section return a dictionary of section data.

The dictionary must include at least {
    'section_key': 'circus_expo'
    'section_display_name': 'Circus Expo'
}

section_display_name will be used to generate link titles in the nav bar.
sek will be used as a css attribute, javascript tie-in, and template import filename.
"""


def _section_course_info(course_id):
    """ Provide data for the corresponding dashboard section """
    course = get_course_by_id(course_id, depth=None)

    section_data = {}
    section_data['section_key'] = 'course_info'
    section_data['section_display_name'] = 'Course Info'
    section_data['course_id'] = course_id
    section_data['course_display_name'] = course.display_name
    section_data['enrollment_count'] = CourseEnrollment.objects.filter(course_id=course_id).count()
    section_data['has_started'] = course.has_started()
    section_data['has_ended'] = course.has_ended()
    section_data['grade_cutoffs'] = "[" + reduce(lambda memo, (letter, score): "{}: {}, ".format(letter, score) + memo , course.grade_cutoffs.items(), "")[:-2] + "]"
    section_data['offline_grades'] = offline_grades_available(course_id)

    try:
        section_data['course_errors'] = [(escape(a), '') for (a,b) in modulestore().get_item_errors(course.location)]
    except Exception:
        section_data['course_errors'] = [('Error fetching errors', '')]

    return section_data


def _section_membership(course_id):
    """ Provide data for the corresponding dashboard section """
    section_data = {
        'section_key': 'membership',
        'section_display_name': 'Membership',
        'enroll_button_url':   reverse('enroll_unenroll', kwargs={'course_id': course_id}),
        'unenroll_button_url': reverse('enroll_unenroll', kwargs={'course_id': course_id}),
        'list_instructors_staff_url': reverse('list_instructors_staff', kwargs={'course_id': course_id}),
        'access_allow_revoke_url': reverse('access_allow_revoke', kwargs={'course_id': course_id}),
        'list_forum_members_url': reverse('list_forum_members', kwargs={'course_id': course_id}),
        'update_forum_role_membership_url': reverse('update_forum_role_membership', kwargs={'course_id': course_id}),
    }
    return section_data


def _section_student_admin(course_id):
    """ Provide data for the corresponding dashboard section """
    section_data = {
        'section_key': 'student_admin',
        'section_display_name': 'Student Admin',
        'get_student_progress_url': reverse('get_student_progress_url', kwargs={'course_id': course_id}),
        'unenroll_button_url': reverse('enroll_unenroll', kwargs={'course_id': course_id}),
        'reset_student_attempts_url': reverse('reset_student_attempts', kwargs={'course_id': course_id}),
    }
    return section_data


def _section_data_download(course_id):
    """ Provide data for the corresponding dashboard section """
    section_data = {
        'section_key': 'data_download',
        'section_display_name': 'Data Download',
        'grading_config_url':             reverse('grading_config', kwargs={'course_id': course_id}),
        'enrolled_students_profiles_url': reverse('enrolled_students_profiles', kwargs={'course_id': course_id}),
    }
    return section_data


def _section_analytics(course_id):
    """ Provide data for the corresponding dashboard section """
    section_data = {
        'section_key': 'analytics',
        'section_display_name': 'Analytics',
        'profile_distributions_url': reverse('profile_distribution', kwargs={'course_id': course_id}),
    }
    return section_data
