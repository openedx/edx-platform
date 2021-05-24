"""
Management command for regenerating certificates with an "unverified" status for users who have an
active approved ID verification.

Example usage:

    $ ./manage.py lms regenerate_unverifed_certs

"""


import logging

from django.core.management.base import BaseCommand

from lms.djangoapps.certificates.generation_handler import can_generate_certificate_task, generate_certificate_task
from lms.djangoapps.certificates.models import CertificateStatuses, GeneratedCertificate
from lms.djangoapps.certificates.tasks import CERTIFICATE_DELAY_SECONDS, generate_certificate
from lms.djangoapps.grades.api import CourseGradeFactory
from lms.djangoapps.verify_student.services import IDVerificationService

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Regenerate certificates with unverified status for users with approved ID verification.
    """

    help = """
    Find all certificates in an "unverified" state for users that have an approved ID verification,
    and regenerate them.

    Use the --noop option to test without actually putting certificates on the queue to be regenerated.
    """

    def add_arguments(self, parser):
        parser.add_argument('-n', '--noop',
                            action='store_true',
                            dest='noop',
                            help="Don't add regeneration request to the queue")

    def handle(self, *args, **options):
        """
        Resubmit certificates with status 'unverified', only for users with an approved ID verification.
        """
        LOGGER.info('Starting to regenerate certificates with status "unverified".')

        queryset = (
            GeneratedCertificate.objects.select_related('user')
        ).filter(status=CertificateStatuses.unverified)

        grade_factory = CourseGradeFactory()
        regenerate_list = [(cert.user, cert.course_id) for cert in queryset]
        user_verified_cache = {}
        regenerate_count = 0
        for user, course_key in regenerate_list:
            if not options['noop']:
                user_is_verified = self._load_user_verified_cache(user, user_verified_cache)
                if user_is_verified:
                    if can_generate_certificate_task(user, course_key):
                        LOGGER.info(
                            'course_id={course_id} is using V2 certificates. Attempt will be made to '
                            'generate a V2 certificate for user_id={user_id}.'.format(
                                course_id=str(course_key), user_id=user.id,
                            ))
                        generate_certificate_task(user, course_key)
                        regenerate_count += 1
                    elif grade_factory.read(user=user, course_key=course_key).passed:
                        LOGGER.info(
                            'Generating certificate for user_id={user_id} in course_id={course_id}'.format(
                                user_id=user.id, course_id=str(course_key),
                            )
                        )
                        kwargs = {'student': str(user.id), 'course_key': str(course_key)}
                        generate_certificate.apply_async(countdown=CERTIFICATE_DELAY_SECONDS, kwargs=kwargs)
                        regenerate_count += 1
                    else:
                        LOGGER.info(
                            'Certificate not regenerated for user_id={user_id} in course_id={course_id} '
                            'as they do not have a passing grade.'.format(
                                user_id=user.id, course_id=str(course_key),
                            )
                        )
                else:
                    LOGGER.info(
                        'Certificate not regenerated for user_id={user_id} in course_id={course_id} '
                        'as they are not verified.'.format(
                            user_id=user.id, course_id=str(course_key),
                        )
                    )
            else:
                LOGGER.info(
                    'Skipping certificate regeneration for user_id={user_id} in course_id={course_id} '
                    'as the noop flag is set.'.format(user_id=user.id, course_id=str(course_key))
                )

        LOGGER.info('Finished regenerating {count} unverified certificates.'.format(count=regenerate_count))

    def _load_user_verified_cache(self, user, user_verified_cache):
        """Determine whether the user is verified, and store the value."""
        user_is_verified = (
            user_verified_cache[user.id] if user.id in user_verified_cache
            else IDVerificationService.user_is_verified(user)
        )
        user_verified_cache[user.id] = user_is_verified
        return user_is_verified

