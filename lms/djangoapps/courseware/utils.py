"""Utility functions that have to do with the courseware."""


import datetime

from lms.djangoapps.commerce.utils import EcommerceService
from pytz import utc

from course_modes.models import CourseMode


def verified_upgrade_deadline_link(user, course=None, course_id=None):
    """
    Format the correct verified upgrade link for the specified ``user``
    in a course.

    One of ``course`` or ``course_id`` must be supplied. If both are specified,
    ``course`` will take priority.

    Arguments:
        user (:class:`~django.contrib.auth.models.User`): The user to display
            the link for.
        course (:class:`.CourseOverview`): The course to render a link for.
        course_id (:class:`.CourseKey`): The course_id of the course to render for.

    Returns:
        The formatted link that will allow the user to upgrade to verified
        in this course.
    """
    if course is not None:
        course_id = course.id
    return EcommerceService().upgrade_url(user, course_id)


def verified_upgrade_link_is_valid(enrollment=None):
    """
    Return whether this enrollment can be upgraded.

    Arguments:
        enrollment (:class:`.CourseEnrollment`): The enrollment under consideration.
            If None, then the enrollment is considered to be upgradeable.
    """
    # Return `true` if user is not enrolled in course
    if enrollment is None:
        return False

    upgrade_deadline = enrollment.upgrade_deadline

    if upgrade_deadline is None:
        return False

    if datetime.datetime.now(utc).date() > upgrade_deadline.date():
        return False

    # Show the summary if user enrollment is in which allow user to upsell
    return enrollment.is_active and enrollment.mode in CourseMode.UPSELL_TO_VERIFIED_MODES
