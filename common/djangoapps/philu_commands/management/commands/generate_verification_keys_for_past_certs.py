"""
Django management command to generate CertificateVerificationKey objects.
"""
from logging import getLogger
from django.core.management.base import BaseCommand

from lms.djangoapps.certificates.models import GeneratedCertificate
from openedx.features.student_certificates.models import CertificateVerificationKey

log = getLogger(__name__)


class Command(BaseCommand):
    help = """
    This command creates a CertificateVerificationKey object for all certificates that aren't linked with a
    CertificateVerificationKey object.

    example:
        manage.py ... generate_verification_keys_for_past_certs
    """

    def handle(self, *args, **options):
        for certificate in GeneratedCertificate.objects.all():
            if not hasattr(certificate, 'certificate_verification_key'):
                log.info('Generating verification key for certificate: {}'.format(certificate.verify_uuid))
                CertificateVerificationKey.objects.create_object(certificate)
