"""
Instructor Views
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

from django.conf import settings
from courseware.access import has_access, get_access_group_name, course_beta_test_group_name
from courseware.courses import get_course_with_access
from django_comment_client.utils import has_forum_access
from instructor.offline_gradecalc import student_grades, offline_grades_available
from django_comment_common.models import Role, FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA
from xmodule.modulestore.django import modulestore


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def instructor_dashboard_2(request, course_id):
    """Display the instructor dashboard for a course."""

    course = get_course_with_access(request.user, course_id, 'staff', depth=None)
    instructor_access = has_access(request.user, course, 'instructor')   # an instructor can manage staff lists
    forum_admin_access = has_forum_access(request.user, course_id, FORUM_ROLE_ADMINISTRATOR)

    context = {
        'course': course,
        'staff_access': True,
        'admin_access': request.user.is_staff,
        'instructor_access': instructor_access,
        'forum_admin_access': forum_admin_access,
        'course_errors': modulestore().get_item_errors(course.location),
        'djangopid': os.getpid(),
        'mitx_version': getattr(settings, 'MITX_VERSION_STRING', ''),
        'offline_grade_log': offline_grades_available(course_id),
        'cohorts_ajax_url': reverse('cohorts', kwargs={'course_id': course_id}),
    }

    return render_to_response('courseware/instructor_dashboard_2.html', context)
