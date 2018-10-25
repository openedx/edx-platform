# -*- coding: utf-8 -*-
"""
Contains code related to computing content gating course duration limits
and course access based on these limits.
"""
from datetime import timedelta

from django.apps import apps
from django.utils import timezone
from django.utils.translation import ugettext as _

from util.date_utils import DEFAULT_SHORT_DATE_FORMAT, strftime_localized
from lms.djangoapps.courseware.access_response import AccessError
from lms.djangoapps.courseware.access_utils import ACCESS_GRANTED
from openedx.core.djangoapps.catalog.utils import get_course_run_details
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


MIN_DURATION = timedelta(weeks=4)
MAX_DURATION = timedelta(weeks=12)


class AuditExpiredError(AccessError):
    """
    Access denied because the user's audit timespan has expired
    """
    def __init__(self, user, course, expiration_date):
        error_code = "audit_expired"
        developer_message = "User {} had access to {} until {}".format(user, course, expiration_date)
        expiration_date = strftime_localized(expiration_date, DEFAULT_SHORT_DATE_FORMAT)
        user_message = _("Access expired on {expiration_date}").format(expiration_date=expiration_date)
        try:
            course_name = CourseOverview.get_from_id(course.id).display_name_with_default
            additional_context_user_message = _("Access to {course_name} expired on {expiration_date}").format(
                course_name=course_name,
                expiration_date=expiration_date
            )
        except CourseOverview.DoesNotExist:
            additional_context_user_message = _("Access to the course you were looking"
                                                "for expired on {expiration_date}").format(
                expiration_date=expiration_date
            )
        super(AuditExpiredError, self).__init__(error_code, developer_message, user_message,
                                                additional_context_user_message)


def get_user_course_expiration_date(user, course):
    """
    Return expiration date for given user course pair.
    Return None if the course does not expire.

    Business Logic:
      - Course access duration is bounded by the min and max duration.
      - If course fields are missing, default course access duration to MIN_DURATION.
    """

    access_duration = MIN_DURATION

    CourseEnrollment = apps.get_model('student.CourseEnrollment')
    enrollment = CourseEnrollment.get_enrollment(user, course.id)
    if enrollment is None or enrollment.mode != 'audit':
        return None

    try:
        # Content availability date is equivalent to max(enrollment date, course start date)
        # for most people. Using the schedule date will provide flexibility to deal with
        # more complex business rules in the future.
        content_availability_date = enrollment.schedule.start
    except CourseEnrollment.schedule.RelatedObjectDoesNotExist:
        content_availability_date = max(enrollment.created, course.start)

    if course.self_paced:
        # The user course expiration date for self paced courses is the
        # content availability date plus the weeks_to_complete field from course-discovery.
        discovery_course_details = get_course_run_details(course.id, ['weeks_to_complete'])
        expected_weeks = discovery_course_details['weeks_to_complete'] or int(MIN_DURATION.days / 7)
        access_duration = timedelta(weeks=expected_weeks)
    elif not course.self_paced and course.end and course.start:
        # The user course expiration date for instructor paced courses is the
        # content availability date plus the duration of the course (course end date minus course start date).
        access_duration = course.end - course.start

    # Course access duration is bounded by the min and max duration.
    access_duration = max(MIN_DURATION, min(MAX_DURATION, access_duration))

    return content_availability_date + access_duration


def check_course_expired(user, course):
    """
    Check if the course expired for the user.
    """
    expiration_date = get_user_course_expiration_date(user, course)
    if expiration_date and timezone.now() > expiration_date:
        return AuditExpiredError(user, course, expiration_date)

    return ACCESS_GRANTED
