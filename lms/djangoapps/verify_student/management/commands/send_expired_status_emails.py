"""
Management command to send expired id-verification status emails.
"""
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from email_marketing.models import EmailMarketingConfiguration
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from lms.djangoapps.verify_student.services import IDVerificationService
from lms.djangoapps.verify_student.tasks import compose_and_send_expired_status_email
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from student.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Sends emails to the learners with expired ID-verification status.
    """
    help = 'Sends emails to the learners with expired ID-verification status.'

    def handle(self, *args, **options):
        """
        Retrieves learners who submitted for ID-Verification and
        sends emails to those learners having expired verification
        status
        """
        email_config = EmailMarketingConfiguration.current()
        if email_config.sailthru_verification_expired_template:
            reverify_url = reverse("verify_student_reverify")
            faq_url = configuration_helpers.get_value(
                'ID_VERIFICATION_SUPPORT_LINK',
                settings.SUPPORT_SITE_LINK
            )

            subject = _("Your {platform_name} ID Verification has Expired").format(
                platform_name=settings.PLATFORM_NAME
            )

            template_vars = {
                'reverify_url': reverify_url,
                'faq_url': faq_url,
                'subject': subject,
                'platform_name': settings.PLATFORM_NAME
            }

            context = {
                'email_config': email_config,
                'template': email_config.sailthru_verification_expired_template,
                'template_vars': template_vars
            }
            sspv = SoftwareSecurePhotoVerification.objects.all()
            for learner in sspv:
                user = User.objects.get(id=learner.user_id)
                status = IDVerificationService.user_status(user=user)['status']
                if status == 'expired':
                    compose_and_send_expired_status_email.delay(user, context)
        else:
            logger.error("Sailthru verification expired template doesn't exist")
