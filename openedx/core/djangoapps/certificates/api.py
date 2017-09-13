"""
The public API for certificates.
"""
from datetime import datetime
from pytz import UTC
from openedx.core.djangoapps.certificates.config import waffle


SWITCHES = waffle.waffle()


def auto_certificate_generation_enabled():
    return SWITCHES.is_enabled(waffle.AUTO_CERTIFICATE_GENERATION)


def _enabled_and_instructor_paced(course):
    if auto_certificate_generation_enabled():
        return not course.self_paced
    return False


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
