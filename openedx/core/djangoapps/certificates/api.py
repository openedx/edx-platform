"""
The public API for certificates.
"""
from datetime import datetime

from pytz import UTC

from course_modes.models import CourseMode
from openedx.core.djangoapps.certificates.config import waffle
from student.models import CourseEnrollment


SWITCHES = waffle.waffle()


def auto_certificate_generation_enabled():
    return SWITCHES.is_enabled(waffle.AUTO_CERTIFICATE_GENERATION)


def _enabled_and_instructor_paced(course):
    if auto_certificate_generation_enabled():
        return not course.self_paced
    return False


def certificates_viewable_for_course(course):
    """
    Returns True if certificates are viewable for any student enrolled in the course, False otherwise.
    """
    if course.self_paced:
        return True
    if (
        course.certificates_display_behavior in ('early_with_info', 'early_no_info')
        or course.certificates_show_before_end
    ):
        return True
    if (
        course.certificate_available_date
        and course.certificate_available_date <= datetime.now(UTC)
    ):
        return True
    if (
        course.certificate_available_date is None
        and course.has_ended()
    ):
        return True
    return False


def is_certificate_valid(certificate):
    """
    Returns True if the student has a valid, verified certificate for this course, False otherwise.
    """
    return CourseEnrollment.is_enrolled_as_verified(certificate.user, certificate.course_id) and certificate.is_valid()


def can_show_certificate_message(course, student, course_grade, certificates_enabled_for_course):
    if not (
        (auto_certificate_generation_enabled() or certificates_enabled_for_course) and
        CourseEnrollment.is_enrolled(student, course.id) and
        certificates_viewable_for_course(course) and
        course_grade.passed
    ):
        return False
    return True


def can_show_certificate_available_date_field(course):
    return _enabled_and_instructor_paced(course)


def display_date_for_certificate(course, certificate):
    if (
        auto_certificate_generation_enabled() and
        not course.self_paced and
        course.certificate_available_date and
        course.certificate_available_date < datetime.now(UTC)
    ):
        return course.certificate_available_date

    return certificate.modified_date
