"""
Handlers for different signals in the student_certificates application.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from common.lib.hubspot_client.client import HubSpotClient
from common.lib.hubspot_client.tasks import task_send_hubspot_email
from lms.djangoapps.certificates.models import GeneratedCertificate
from openedx.features.student_certificates.models import CertificateVerificationKey
from openedx.features.student_certificates.signals import USER_CERTIFICATE_DOWNLOADABLE
from openedx.features.student_certificates.tasks import task_create_certificate_img_and_upload_to_s3

log = logging.getLogger(__name__)


@receiver(post_save, sender=GeneratedCertificate)
def generate_certificate_img(instance, created, **_kwargs):
    if not created:
        task_create_certificate_img_and_upload_to_s3.delay(instance.verify_uuid)


@receiver(post_save, sender=GeneratedCertificate)
def generate_certificate_verification_key(instance, created, **_kwargs):
    if created and not hasattr(instance, 'certificate_verification_key'):
        CertificateVerificationKey.objects.create_object(instance)


@receiver(USER_CERTIFICATE_DOWNLOADABLE)
def send_email_user_certificate_downloadable(
    sender, first_name, display_name, certificate_reverse_url, user_email, *args, **kwargs
):  # pylint: disable=unused-argument
    """
    Send email containing course certificate to the specified user

    Arguments:
        sender: Sender that triggered or sent the signal
        first_name (str): First name of the user
        display_name (str): Display name of the user
        certificate_reverse_url (str): Url of the downloadable ceritificate
        user_email (str): Email of the recipient user

    Returns:
        None
    """
    context = {
        'emailId': HubSpotClient.CERTIFICATE_READY_TO_DOWNLOAD,
        'message': {
            'to': user_email
        },
        'customProperties': {
            'course_name': display_name,
            'certificate_url': certificate_reverse_url,
            'first_name': first_name
        }
    }
    task_send_hubspot_email.delay(context)
