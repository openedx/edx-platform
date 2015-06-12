"""
This file contains receivers of course publication signals.
"""

import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext as _

from edxmako.shortcuts import render_to_string
from microsite_configuration import microsite
from openedx.core.djangoapps.credit.models import CreditEligibility
from openedx.core.djangoapps.user_api.accounts.api import get_account_settings
from xmodule.modulestore.django import SignalHandler


log = logging.getLogger(__name__)


@receiver(SignalHandler.course_published)
def listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """Receive 'course_published' signal and kick off a celery task to update
    the credit course requirements.
    """

    # Import here, because signal is registered at startup, but items in tasks
    # are not yet able to be loaded
    from .tasks import update_course_requirements

    update_course_requirements.delay(unicode(course_key))


@receiver(post_save, sender=CreditEligibility)
def send_credit_eligibility_email(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    """Receive post_save signal for 'CreditEligibility' and sends email to user for being eligible for
    the course if 'CreditEligibility' object created successfully
    """
    if created:
        user = None
        try:
            user = User.objects.get(username=instance.username)
        except User.DoesNotExist:
            log.debug('No user with %s exist', instance.username)
        account_settings = get_account_settings(user)

        context = {
            'full_name': account_settings['name'],
            'platform_name': settings.PLATFORM_NAME,
            'course_key': instance.course.course_key,
        }

        subject = _("Verification photos received")
        message = render_to_string('emails/credit_eligibility_confirmation.txt', context)
        from_address = microsite.get_value('default_from_email', settings.DEFAULT_FROM_EMAIL)
        to_address = account_settings['email']

        send_mail(subject, message, from_address, [to_address], fail_silently=False)
