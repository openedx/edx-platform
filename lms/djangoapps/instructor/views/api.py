"""
Instructor Dashboard API views

Non-html views which the instructor dashboard requests.

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
from django.http import HttpResponse, HttpResponseBadRequest

from django.conf import settings
from courseware.access import has_access, get_access_group_name, course_beta_test_group_name
from courseware.courses import get_course_with_access
from django_comment_client.utils import has_forum_access
from instructor.offline_gradecalc import student_grades, offline_grades_available
from django_comment_common.models import Role, FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA
from xmodule.modulestore.django import modulestore
from student.models import CourseEnrollment
import xmodule.graders as xmgraders
from django.contrib.auth.models import User, Group
from student.models import CourseEnrollment


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def grading_config(request, course_id):
    """
    Respond with json which contains a html formatted grade summary.

    TODO maybe this shouldn't be html already
    """
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)
    grading_config_summary = _dump_grading_context(course)

    response_payload = {
        'course_id': course_id,
        'grading_config_summary': grading_config_summary,
    }
    response = HttpResponse(json.dumps(response_payload), content_type="application/json")
    return response


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def enrolled_students_profiles(request, course_id):
    """
    Respond with json which contains a summary of all enrolled students profile information.

    TODO respond to csv requests as well
    TODO accept requests for different attribute sets
    """

    enrollments = CourseEnrollment.objects.filter(course_id=course_id)
    students = [enrollment.user for enrollment in enrollments]

    STUDENT_FEATURES = ['username', 'first_name', 'last_name', 'is_staff', 'email']
    PROFILE_FEATURES = ['year_of_birth', 'gender', 'level_of_education']

    def extract_student(student):
        student_dict = dict((feature, getattr(student, feature)) for feature in STUDENT_FEATURES)
        profile = student.profile
        profile_dict = dict((feature, getattr(profile, feature)) for feature in PROFILE_FEATURES)
        student_dict.update(profile_dict)
        return student_dict

    response_payload = {
        'course_id':        course_id,
        'students':         [extract_student(student) for student in students],
        'STUDENT_FEATURES': STUDENT_FEATURES,
        'PROFILE_FEATURES': PROFILE_FEATURES,
        'all_features':     STUDENT_FEATURES + PROFILE_FEATURES,
    }
    response = HttpResponse(json.dumps(response_payload), content_type="application/json")
    return response


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def enrolled_students_choices_numbers(request, course_id):
    """
    Respond with json of the distribution of students on fields select fields which have choices.

    TODO respond to csv requests as well
    TODO accept requests for different attribute sets
    """

    EASY_CHOICE_FEATURES = ['year_of_birth', 'gender', 'level_of_education', 'language']
    OPEN_CHOICE_FEATURES = ['language', 'location/mailing_address']
    raise NotImplementedError()


def _dump_grading_context(course):
    """
    Dump information about course grading context (eg which problems are graded in what assignments)
    Very useful for debugging grading_policy.json and policy.json
    """
    msg = "-----------------------------------------------------------------------------\n"
    msg += "Course grader:\n"

    msg += '%s\n' % course.grader.__class__
    graders = {}
    if isinstance(course.grader, xmgraders.WeightedSubsectionsGrader):
        msg += '\n'
        msg += "Graded sections:\n"
        for subgrader, category, weight in course.grader.sections:
            msg += "  subgrader=%s, type=%s, category=%s, weight=%s\n" % (subgrader.__class__, subgrader.type, category, weight)
            subgrader.index = 1
            graders[subgrader.type] = subgrader
    msg += "-----------------------------------------------------------------------------\n"
    msg += "Listing grading context for course %s\n" % course.id

    gc = course.grading_context
    msg += "graded sections:\n"

    msg += '%s\n' % gc['graded_sections'].keys()
    for (gs, gsvals) in gc['graded_sections'].items():
        msg += "--> Section %s:\n" % (gs)
        for sec in gsvals:
            s = sec['section_descriptor']
            format = getattr(s.lms, 'format', None)
            aname = ''
            if format in graders:
                g = graders[format]
                aname = '%s %02d' % (g.short_label, g.index)
                g.index += 1
            elif s.display_name in graders:
                g = graders[s.display_name]
                aname = '%s' % g.short_label
            notes = ''
            if getattr(s, 'score_by_attempt', False):
                notes = ', score by attempt!'
            msg += "      %s (format=%s, Assignment=%s%s)\n" % (s.display_name, format, aname, notes)
    msg += "all descriptors:\n"
    msg += "length=%d\n" % len(gc['all_descriptors'])
    msg = '<pre>%s</pre>' % msg.replace('<','&lt;')
    return msg
