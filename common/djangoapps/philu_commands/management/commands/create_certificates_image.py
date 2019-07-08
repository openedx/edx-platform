from datetime import datetime

from django.core.management.base import BaseCommand

from certificates.models import GeneratedCertificate
from openedx.features.student_certificates.tasks import task_create_certificate_img_and_upload_to_s3


class Command(BaseCommand):
    help = 'Create and upload(to s3) image(s) of specific certificate(s)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--uuid',
            action='append',
            help='Create images against mentioned uuid(s) of certificate(s)',
        )
        parser.add_argument(
            '--after',
            const='str',
            nargs='?',
            help='Create images of all certificates generated after given date like (15/09/1995) - (day/month/year)',
        )

    def handle(self, *args, **options):
        opt_after = options['after']
        opt_uuid = options['uuid']
        certificates = []

        if opt_after:
            after_date = datetime.strptime(opt_after, '%d/%m/%Y')
            certificates = GeneratedCertificate.objects.filter(created_date__gte=after_date)
        elif opt_uuid:
            certificates = GeneratedCertificate.objects.filter(verify_uuid__in=opt_uuid)
        else:
            certificates = GeneratedCertificate.objects.all()

        for certificate in certificates:
            task_create_certificate_img_and_upload_to_s3.delay(verify_uuid=certificate.verify_uuid)
