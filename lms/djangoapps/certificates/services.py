"""
Certificate service
"""


import logging

from django.core.exceptions import ObjectDoesNotExist
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.certificates.generation_handler import is_on_certificate_allowlist
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.utils import _get_key

log = logging.getLogger(__name__)


class CertificateService:
    """
    User Certificate service
    """

    def invalidate_certificate(self, user_id, course_key_or_id):
        """
        Invalidate the user certificate in a given course if it exists and the user is not on the allowlist for this
        course run.
        """
        course_key = _get_key(course_key_or_id, CourseKey)
        if is_on_certificate_allowlist(user_id, course_key):
            log.info(f'User {user_id} is on the allowlist for {course_key}. The certificate will not be invalidated.')
            return False

        try:
            generated_certificate = GeneratedCertificate.objects.get(
                user=user_id,
                course_id=course_key
            )
            generated_certificate.invalidate(source='certificate_service')
        except ObjectDoesNotExist:
            log.warning(
                'Invalidation failed because a certificate for user %d in course %s does not exist.',
                user_id,
                course_key
            )
            return False

        return True
