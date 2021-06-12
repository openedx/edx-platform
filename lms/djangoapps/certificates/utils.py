"""
Certificates utilities
"""

import logging

from django.conf import settings
from django.urls import reverse
from eventtracking import tracker
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.certificates.models import GeneratedCertificate
from openedx.core.djangoapps.content.course_overviews.api import get_course_overview

log = logging.getLogger(__name__)


def emit_certificate_event(event_name, user, course_id, course_overview=None, event_data=None):
    """
    Utility function responsible for emitting certificate events.

    We currently track the following events:
    - `edx.certificate.created` - Emit when a course certificate with the `downloadable` status has been awarded to a
                                  learner.
    - `edx.certificate.revoked`- Emit when a course certificate with the `downloadable` status has been taken away from
                                 a learner.
    - `edx.certificate.shared` - Emit when a learner shares their course certificate to social media (LinkedIn,
                                 Facebook, or Twitter).
    - `edx.certificate.evidence_visisted` - Emit when a user (other than the learner who owns a certificate) views a
                                            course certificate (e.g., someone views a course certificate shared on a
                                            LinkedIn profile).

    Args:
        event_name (String) - Text describing the action/event that we are tracking. Examples include `revoked`,
                              `created`, etc.
        user (User) - The User object of the learner associated with this event.
        course_id (CourseLocator) - The course-run key associated with this event.
        course_overview (CourseOverview) - Optional. The CourseOverview of the course-run associated with this event.
        event_data (dictionary) - Optional. Dictionary containing any additional data we want to be associated with an
                                  event.
    """
    event_name = '.'.join(['edx', 'certificate', event_name])

    if not course_overview:
        course_overview = get_course_overview(course_id)

    context = {
        'org_id': course_overview.org,
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

    course_overview = _course_from_key(course_id)
    if not course_overview:
        return url

    if has_html_certificates_enabled(course_overview):
        url = _certificate_html_url(uuid)
    else:
        url = _certificate_download_url(user_id, course_id, user_certificate=user_certificate)
    return url


def has_html_certificates_enabled(course_overview):
    """
    Returns True if HTML certificates are enabled in a course run.
    """
    if not settings.FEATURES.get('CERTIFICATES_HTML_VIEW', False):
        return False
    return course_overview.cert_html_view_enabled


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
    return get_course_overview(_safe_course_key(course_key))


def _safe_course_key(course_key):
    """
    Returns the course key
    """
    if not isinstance(course_key, CourseKey):
        return CourseKey.from_string(course_key)
    return course_key
