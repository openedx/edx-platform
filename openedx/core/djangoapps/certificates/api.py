"""
The public API for certificates.
"""


import logging
from datetime import datetime
from pytz import UTC

from lms.djangoapps.certificates import api as certs_api
from lms.djangoapps.certificates.data import CertificateStatuses
from openedx.core.djangoapps.certificates.config import waffle
from common.djangoapps.student.models import CourseEnrollment
from xmodule.data import CertificatesDisplayBehaviors

log = logging.getLogger(__name__)

SWITCHES = waffle.waffle()


def auto_certificate_generation_enabled():
    return SWITCHES.is_enabled(waffle.AUTO_CERTIFICATE_GENERATION)


def _enabled_and_instructor_paced(course):
    if auto_certificate_generation_enabled():
        return not course.self_paced
    return False


def is_certificate_valid(certificate):
    """
    Returns True if the student has a valid, verified certificate for this course, False otherwise.
    """
    return CourseEnrollment.is_enrolled_as_verified(certificate.user, certificate.course_id) and certificate.is_valid()


def can_show_certificate_message(course, student, course_grade, certificates_enabled_for_course):
    """
    Returns True if a course certificate message can be shown
    """
    is_allowlisted = certs_api.is_on_allowlist(student, course.id)
    auto_cert_gen_enabled = auto_certificate_generation_enabled()
    has_active_enrollment = CourseEnrollment.is_enrolled(student, course.id)
    certificates_are_viewable = certs_api.certificates_viewable_for_course(course)

    return (
        (auto_cert_gen_enabled or certificates_enabled_for_course) and
        has_active_enrollment and
        certificates_are_viewable and
        (course_grade.passed or is_allowlisted)
    )


def can_show_certificate_available_date_field(course):
    return _enabled_and_instructor_paced(course)


def _course_uses_available_date(course):
    return (
        can_show_certificate_available_date_field(course)
        and course.certificates_display_behavior == CertificatesDisplayBehaviors.END_WITH_DATE
    )


def available_date_for_certificate(course, certificate, certificate_available_date=None):
    """
    Returns the available date to use with a certificate

    Arguments:
        course (CourseOverview): The course we're checking
        certificate (GeneratedCertificate): The certificate we're getting the date for
        certificate_available_date (datetime): An optional date to override the from the course overview.
    """
    if _course_uses_available_date(course):
        return certificate_available_date or course.certificate_available_date
    return certificate.modified_date


def display_date_for_certificate(course, certificate):
    if _course_uses_available_date(course) and course.certificate_available_date < datetime.now(UTC):
        return course.certificate_available_date
    return certificate.modified_date


def is_valid_pdf_certificate(cert_data):
    return cert_data.cert_status == CertificateStatuses.downloadable and cert_data.download_url
