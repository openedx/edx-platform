"""
Management command to regenerate unverified certificates when a course
transitions to honor code.
"""
import logging
import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.certificates.generation_handler import generate_certificate_task
from lms.djangoapps.certificates.models import GeneratedCertificate
from openedx.core.djangoapps.agreements.toggles import is_integrity_signature_enabled

log = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    """
    Management command to regenerate unverified certificates when a course
    transitions to honor code.
    """
    def add_arguments(self, parser):
        parser.add_argument(
            '-c', '--course-keys',
            nargs='+',
            dest='course_keys',
            help='course run key or space separated list of course run keys'
        )
        parser.add_argument(
            '--batch_size',
            action='store',
            dest='batch_size',
            type=int,
            default=200,
            help='Number of certs per batch'
        )
        parser.add_argument(
            '--sleep_seconds',
            action='store',
            dest='sleep_seconds',
            type=int,
            default=20,
            help='Seconds to sleep between batches'
        )

    def handle(self, *args, **options):
        courses_str = options['course_keys']
        if not courses_str:
            raise CommandError('You must specify a course-key or keys')

        batch_size = options['batch_size']
        sleep_seconds = options['sleep_seconds']
        course_keys = []
        for course_id in courses_str:
            # Parse the serialized course key into a CourseKey
            try:
                course_key = CourseKey.from_string(course_id)
            except InvalidKeyError as e:
                raise CommandError(f'{course_id} is not a valid course-key') from e
            course_keys.append(course_key)

        count = 0
        for key in course_keys:
            #rolling count to maintain batch_size across courses
            count = _handle_course(key, batch_size, sleep_seconds, count)
        return f'{count}'


def _handle_course(course_key, batch_size, sleep_seconds, count):
    """
    Regenerates unverified status certificates for the designated course with delay seconds between certs.
    Returns how many certs were originally unverified and regenerated.
    """

    if not is_integrity_signature_enabled(course_key):
        log.warning(f'Skipping {course_key} which does not have honor code enabled')
        return 0

    certs = GeneratedCertificate.objects.filter(
        course_id=course_key,
        status=CertificateStatuses.unverified,
    )

    log.info(f'Regenerating {len(certs)} unverified certificates for {course_key}')

    for cert in certs:
        user = User.objects.get(id=cert.user_id)
        generate_certificate_task(user, course_key, generation_mode='batch', delay_seconds=0)
        count += 1
        if count % batch_size == 0:
            time.sleep(sleep_seconds)
    return count
