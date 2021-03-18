"""
Helper functions for specializations app
"""
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
from opaque_keys.edx.keys import CourseKey

from common.lib.discovery_client.client import DiscoveryClient
from lms.djangoapps.certificates.models import CertificateStatuses
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.timed_notification.core import get_course_first_chapter_link
from student.helpers import cert_info
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore

DISCOVERY_DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def date_time_from_now(delta_days):
    """
    Get delta date from now in string format
    Args:
        delta_days (int): No of days in past or future

    Returns:
        String date
    """
    return (datetime.now() + timedelta(days=delta_days)).strftime(DISCOVERY_DATE_FORMAT)


def date_from_str(date_str, date_format=DISCOVERY_DATE_FORMAT):
    return datetime.strptime(date_str, date_format)


def get_program_courses(user, specialization_uuid, detail=False):
    """
    Get course run in a program and data related to programs
    Args:
        user (object): User object
        specialization_uuid (str): Program uuid
        detail (boolean): True if want detailed info in course dict

    Returns:
        A tuple of courses and context from discovery programs
    """
    context = get_program_from_discovery(specialization_uuid)
    courses = []

    if not user.is_authenticated:
        return context, courses

    for course in [course for course in context.get('courses', []) if course.get('course_runs', [])]:
        course_rerun = get_open_course_rerun(course['course_runs'])
        course_id = CourseKey.from_string(course_rerun['key'])
        course_rerun['course_id'] = course_id
        course_rerun['enrolled'] = CourseEnrollment.is_enrolled(user, course_id)

        if detail:
            course_rerun['first_chapter_link'] = get_first_chapter_link(course_id)
            course_rerun['completed'], course_rerun['in_progress'] = is_course_completed_or_in_progress(course_id, user)

        courses.append(course_rerun)

    context.update({'courses': courses})
    return context, courses


def get_open_course_rerun(course_runs):
    """
    Sort list of course reruns and get first open rerun
    Args:
        course_runs (list): list of all reruns in a course

    Returns:
        Open course rerun
    """
    open_course_rerun_list = [
        rerun for rerun in course_runs
        if rerun['enrollment_start'] and rerun['enrollment_end'] and date_from_str(
            rerun['enrollment_start']) <= datetime.now() <= date_from_str(rerun['enrollment_end'])
    ]

    opened = bool(open_course_rerun_list)
    course_rerun = (
        sorted(
            open_course_rerun_list, key=lambda open_rerun: date_from_str(open_rerun['enrollment_start'])
        )[0] if opened else course_runs[0]
    )

    course_rerun['opened'] = opened
    return course_rerun


def get_first_chapter_link(course_id):
    """
    Get first chapter link for a course run

    Args:
        course_id (CourseKey): Course key object

    Returns:
        String, link
    """
    current_course = modulestore().get_course(course_id)
    return get_course_first_chapter_link(current_course) if current_course else ''


def is_course_completed_or_in_progress(course_id, user):
    """
    Check if course is completed or not, if not then is course started by learner or not yet started.
    Args:
        course_id (CourseKey): Course key object
        user (object): Current user

    Returns:
        Tuple of booleans
    """

    course_overview = CourseOverview.get_from_id(course_id)
    certificate_info = cert_info(user, course_overview)
    certificate_with_passing_status = CertificateStatuses.is_passing_status(certificate_info.get('status'))
    grades = CourseGradeFactory().read(user=user, course_key=course_id)

    is_completed = certificate_with_passing_status or grades.passed
    is_in_progress = 0.0 < grades.percent and not is_completed
    return is_completed, is_in_progress


def get_program_from_discovery(specialization_uuid):
    """
    Get program from discovery client by uuid

    Args:
        specialization_uuid (str): uuid of specialization

    Returns:
        Programs detail from discovery
    """
    try:
        program_context = DiscoveryClient().get_program(specialization_uuid)
    except ValidationError as exc:
        raise HttpResponseBadRequest(exc.message)

    return program_context
