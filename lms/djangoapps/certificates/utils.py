"""
Certificates utilities
"""

import logging

from django.conf import settings
from django.urls import reverse
from eventtracking import tracker
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.certificates.models import GeneratedCertificate
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)


def emit_certificate_event(event_name, user, course_id, course=None, event_data=None):
    """
    Emits certificate event.

    Documentation (that is not up to date) for these events can be found here:
    https://github.com/edx/edx-documentation/blob/master/en_us/data/source/internal_data_formats/tracking_logs/student_event_types.rst # pylint: disable=line-too-long
    """
    event_name = '.'.join(['edx', 'certificate', event_name])
    if course is None:
        course = modulestore().get_course(course_id, depth=0)
    context = {
        'org_id': course.org,
        'course_id': str(course_id)
    }

    data = {
        'user_id': user.id,
        'course_id': str(course_id),
        'certificate_url': get_certificate_url(user.id, course_id, uuid=event_data['certificate_id'])
    }
    event_data = event_data or {}
    event_data.update(data)

    with tracker.get_tracker().context(event_name, context):
        tracker.emit(event_name, event_data)


def get_certificate_url(user_id=None, course_id=None, uuid=None, user_certificate=None):
    """
    Returns the certificate URL
    """
    url = ''

    course = _course_from_key(course_id)
    if not course:
        return url

    if has_html_certificates_enabled(course):
        url = _certificate_html_url(uuid)
    else:
        url = _certificate_download_url(user_id, course_id, user_certificate=user_certificate)
    return url


def has_html_certificates_enabled(course):
    """
    Returns True if HTML certificates are enabled
    """
    if not settings.FEATURES.get('CERTIFICATES_HTML_VIEW', False):
        return False
    return course.cert_html_view_enabled


def _certificate_html_url(uuid):
    """
    Returns uuid based certificate URL.
    """
    return reverse(
        'certificates:render_cert_by_uuid', kwargs={'certificate_uuid': uuid}
    ) if uuid else ''


def _certificate_download_url(user_id, course_id, user_certificate=None):
    """
    Returns the certificate download URL
    """
    if not user_certificate:
        try:
            user_certificate = GeneratedCertificate.eligible_certificates.get(
                user=user_id,
                course_id=_safe_course_key(course_id)
            )
        except GeneratedCertificate.DoesNotExist:
            log.critical(
                'Unable to lookup certificate\n'
                'user id: %s\n'
                'course: %s', str(user_id), str(course_id)
            )

    if user_certificate:
        return user_certificate.download_url

    return ''


def _course_from_key(course_key):
    """
    Returns the course overview
    """
    return CourseOverview.get_from_id(_safe_course_key(course_key))


def _safe_course_key(course_key):
    """
    Returns the course key
    """
    if not isinstance(course_key, CourseKey):
        return CourseKey.from_string(course_key)
    return course_key
