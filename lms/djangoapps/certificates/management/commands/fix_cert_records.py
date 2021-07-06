"""
(Temporary) Management command used to fix some incorrectly generated certificate records created as a side effect of
CR-3792.
"""
import datetime
import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from lms.djangoapps.certificates.generation_handler import _generate_certificate_task
from lms.djangoapps.certificates.models import GeneratedCertificate

log = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    """
    Temporary Management command to fix the incorrect mode on a number of records in the
    `CERTIFICATES_GENERATEDCERTIFICATE table.
    """
    def add_arguments(self, parser):
        parser.add_argument(
            '-l', '--limit',
            metavar='LIMIT',
            dest='limit',
            help='number of records to process at once'
        )

    def handle(self, *args, **options):
        if options.get('limit'):
            limit = int(options['limit'])
        else:
            limit = 1000

        # We started creating the incorrect certificate records around May 10th, 2021.
        certs = GeneratedCertificate.objects.filter(
            mode='honor',
            created_date__gte=datetime.date(2021, 5, 10)
        ).order_by(
            'created_date'
        )[:limit]

        for cert in certs:
            user = User.objects.get(id=cert.user_id)
            course_id = cert.course_id

            _generate_certificate_task(
                user=user,
                course_key=course_id,
                status=cert.status,
                generation_mode='batch'
            )
