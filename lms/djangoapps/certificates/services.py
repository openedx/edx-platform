"""
Certificate service
"""


import logging

from django.core.exceptions import ObjectDoesNotExist
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.utils import _get_key

from .models import GeneratedCertificate

log = logging.getLogger(__name__)


class CertificateService(object):
    """
    User Certificate service
    """

    def invalidate_certificate(self, user_id, course_key_or_id):
        """
        Invalidate the user certificate in a given course if it exists.
        """
        course_key = _get_key(course_key_or_id, CourseKey)
        try:
            generated_certificate = GeneratedCertificate.objects.get(
                user=user_id,
                course_id=course_key
            )
            generated_certificate.invalidate()
            log.info(
                u'Certificate invalidated for user %d in course %s',
                user_id,
                course_key
            )
        except ObjectDoesNotExist:
            log.warning(
                u'Invalidation failed because a certificate for user %d in course %s does not exist.',
                user_id,
                course_key
            )
