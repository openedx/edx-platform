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

from django.conf import settings
from courseware.access import has_access, get_access_group_name, course_beta_test_group_name
from courseware.courses import get_course_with_access
from django_comment_client.utils import has_forum_access
from instructor.offline_gradecalc import student_grades, offline_grades_available
from django_comment_common.models import Role, FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA
from xmodule.modulestore.django import modulestore
from student.models import CourseEnrollment


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def instructor_dashboard_2(request, course_id):
    """Display the instructor dashboard for a course."""

    course = get_course_with_access(request.user, course_id, 'staff', depth=None)
    instructor_access = has_access(request.user, course, 'instructor')   # an instructor can manage staff lists
    forum_admin_access = has_forum_access(request.user, course_id, FORUM_ROLE_ADMINISTRATOR)

    section_data = {
        'course_info':   _section_course_info(request, course_id),
        'enrollment':    _section_enrollment(course_id),
        'student_admin': _section_student_admin(course_id),
        'data_download': _section_data_download(course_id),
        'analytics': _section_analytics(course_id),
    }

    context = {
        'course': course,
        'staff_access': True,
        'admin_access': request.user.is_staff,
        'instructor_access': instructor_access,
        'forum_admin_access': forum_admin_access,
        'djangopid': os.getpid(),
        'mitx_version': getattr(settings, 'MITX_VERSION_STRING', ''),
        'cohorts_ajax_url': reverse('cohorts', kwargs={'course_id': course_id}),
        'section_data': section_data
    }

    return render_to_response('courseware/instructor_dashboard_2/instructor_dashboard_2.html', context)


def _section_course_info(request, course_id):
    """ Provide data for the corresponding dashboard section """
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)

    section_data = {}
    section_data['course_id'] = course_id
    section_data['display_name'] = course.display_name
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


def _section_enrollment(course_id):
    """ Provide data for the corresponding dashboard section """
    section_data = {}
    section_data['placeholder'] = "Enrollment content."
    return section_data


def _section_student_admin(course_id):
    """ Provide data for the corresponding dashboard section """
    section_data = {}
    section_data['placeholder'] = "Student Admin content."
    return section_data


def _section_data_download(course_id):
    """ Provide data for the corresponding dashboard section """
    section_data = {
        'grading_config_url':             reverse('grading_config', kwargs={'course_id': course_id}),
        'enrolled_students_profiles_url': reverse('enrolled_students_profiles', kwargs={'course_id': course_id}),
    }
    return section_data


def _section_analytics(course_id):
    """ Provide data for the corresponding dashboard section """
    section_data = {
        'profile_distributions_url': reverse('profile_distribution', kwargs={'course_id': course_id}),
    }
    return section_data
