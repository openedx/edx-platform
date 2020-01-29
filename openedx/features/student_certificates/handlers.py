import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from common.lib.mandrill_client.client import MandrillClient
from lms.djangoapps.certificates.models import GeneratedCertificate

from models import CertificateVerificationKey
from openedx.features.student_certificates.signals import USER_CERTIFICATE_DOWNLOADABLE
from tasks import task_create_certificate_img_and_upload_to_s3

log = logging.getLogger(__name__)


@receiver(post_save, sender=GeneratedCertificate)
def generate_certificate_img(instance, created, **kwargs):
    if not created:
        task_create_certificate_img_and_upload_to_s3.delay(instance.verify_uuid)


@receiver(post_save, sender=GeneratedCertificate)
def generate_certificate_verification_key(instance, created, **kwargs):
    if created and not hasattr(instance, 'certificate_verification_key'):
        CertificateVerificationKey.objects.create_object(instance)


@receiver(USER_CERTIFICATE_DOWNLOADABLE)
def send_email_user_certificate_downloadable(sender, first_name, display_name, certificate_reverse_url, user_email,
                                             *args, **kwargs):
    template = MandrillClient.DOWNLOAD_CERTIFICATE

    context = dict(first_name=first_name, course_name=display_name,
                   certificate_url=certificate_reverse_url)
    try:
        MandrillClient().send_mail(template, user_email, context)
    except Exception as e:
        # Mandrill errors are thrown as exceptions
        log.error(
            'Unable to send email for USER_CERTIFICATE_DOWNLOADABLE signal: {class_name} - {exception_object}'.format(
                class_name=e.__class__, exception_object=e))
