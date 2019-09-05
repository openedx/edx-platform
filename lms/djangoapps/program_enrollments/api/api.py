# -*- coding: utf-8 -*-
"""
ProgramEnrollment internal API intended for Enterprise API.

This is not part of the program_enrollments Python API.

The Enterprise API currently depends on this module being present with these
functions, as implemented in ./utils.py. This module will be refactored
away in https://openedx.atlassian.net/browse/ENT-2294
"""
from __future__ import absolute_import, unicode_literals

from lms.djangoapps.program_enrollments.rest_api.v1.utils import get_course_run_url as get_course_run_url_util
from lms.djangoapps.program_enrollments.rest_api.v1.utils import get_due_dates as get_due_dates_util
from lms.djangoapps.program_enrollments.rest_api.v1.utils import get_emails_enabled as get_emails_enabled_util


def get_due_dates(request, course_key, user):
    """
    Get due date information for a user for blocks in a course.
    Arguments:
        request: the request object
        course_key (CourseKey): the CourseKey for the course
        user: the user object for which we want due date information
    Returns:
        due_dates (list): a list of dictionaries containing due date information
            keys:
                name: the display name of the block
                url: the deep link to the block
                date: the due date for the block
    """
    return get_due_dates_util(request, course_key, user)


def get_course_run_url(request, course_id):
    """
    Get the URL to a course run.
    Arguments:
        request: the request object
        course_id (string): the course id of the course
    Returns:
        (string): the URL to the course run associated with course_id
    """
    return get_course_run_url_util(request, course_id)


def get_emails_enabled(user, course_id):
    """
    Get whether or not emails are enabled in the context of a course.
    Arguments:
        user: the user object for which we want to check whether emails are enabled
        course_id (string): the course id of the course
    Returns:
        (bool): True if emails are enabled for the course associated with course_id for the user;
        False otherwise
    """
    return get_emails_enabled_util(user, course_id)
