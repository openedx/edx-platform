"""
Course certificate generation

These methods generate course certificates (they create a new course certificate if it does not yet exist, or update the
existing cert if it does already exist).

For now, these methods deal primarily with allowlist certificates, and are part of the V2 certificates revamp.

These method should be called from tasks.
"""

import logging
import random
from uuid import uuid4

from capa.xqueue_interface import make_hashkey
from xmodule.modulestore.django import modulestore

from common.djangoapps.student.models import CourseEnrollment, UserProfile
from lms.djangoapps.certificates.models import CertificateStatuses, GeneratedCertificate
from lms.djangoapps.certificates.utils import emit_certificate_event
from lms.djangoapps.grades.api import CourseGradeFactory

log = logging.getLogger(__name__)


def generate_allowlist_certificate(user, course_key):
    """
    Generate an allowlist certificate for this user, in this course run. This method should be called from a task.
    """
    cert = _generate_certificate(user, course_key)

    if CertificateStatuses.is_passing_status(cert.status):
        # Emit a certificate event. Note that the two options for generation_mode are "self" (implying the user
        # generated the cert themself) and "batch" for everything else.
        event_data = {
            'user_id': user.id,
            'course_id': str(course_key),
            'certificate_id': cert.verify_uuid,
            'enrollment_mode': cert.mode,
            'generation_mode': 'batch'
        }
        emit_certificate_event(event_name='created', user=user, course_id=course_key, event_data=event_data)

    return cert


def _generate_certificate(user, course_id):
    """
    Generate a certificate for this user, in this course run.
    """
    profile = UserProfile.objects.get(user=user)
    profile_name = profile.name

    course = modulestore().get_course(course_id, depth=0)
    course_grade = CourseGradeFactory().read(user, course)
    enrollment_mode, __ = CourseEnrollment.enrollment_mode_for_user(user, course_id)
    key = make_hashkey(random.random())
    uuid = uuid4().hex

    cert, created = GeneratedCertificate.objects.update_or_create(
        user=user,
        course_id=course_id,
        defaults={
            'user': user,
            'course_id': course_id,
            'mode': enrollment_mode,
            'name': profile_name,
            'status': CertificateStatuses.downloadable,
            'grade': course_grade.percent,
            'download_url': '',
            'key': key,
            'verify_uuid': uuid
        }
    )

    if created:
        created_msg = 'Certificate was created.'
    else:
        created_msg = 'Certificate already existed and was updated.'
    log.info(
        'Generated certificate with status {status} for {user} : {course}. {created_msg}'.format(
            status=cert.status,
            user=cert.user.id,
            course=cert.course_id,
            created_msg=created_msg
        ))
    return cert
