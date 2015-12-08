import requests

from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver

from util.model_utils import get_changed_fields_dict

import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=settings.AUTH_USER_MODEL,  dispatch_uid="user.pre_save.send_login_to_AMC")
def send_login_to_AMC(sender, instance, update_fields, **kwargs):
    """
    We only want to ping AMC if this is the user's first login.
    When the old value of last_login is None, we have a winner.
    """
    if update_fields and 'last_login' in update_fields:
        changed = get_changed_fields_dict(instance, sender)
        old_last = changed['last_login']
        logger.info("old last login: {}".format(old_last))
        if not old_last:
            # ping AMC
            url_base = settings.FEATURES.get('APPSEMBLER_AMC_API_BASE', '')
            url_suffix = settings.FEATURES.get('APPSEMBLER_FIRST_LOGIN_API', '')
            if not url_base:
                logger.warning("APPSEMBLER_AMC_API_BASE is not set")
            if not url_suffix:
                logger.warning("APPSEMBLER_FIRST_LOGIN_API is not set")
            url = url_base + url_suffix
            datetime_to_send = instance.last_login.isoformat()
            payload = {
                'email':instance.email,
                'first_logged_into_edx': datetime_to_send,
                'secret_key': settings.FEATURES['APPSEMBLER_SECRET_KEY']
            }
            try:
                response = requests.post(url, data=payload)
                if response.status_code == 200:
                    logger.info("User {} first login sent to AMC.".format(instance.email))
                elif response.status_code == 404:
                    logger.warning("User {} first login sent to AMC but not to Hubspot.".format(instance.email))
                else:
                    logger.warning("User first login NOT received by AMC for user {}".format(instance.email))

            except requests.exceptions.RequestException as e:
                logger.info(e.strerror)
                logger.info(e.message)
                logger.warning("Could not connect to AMC; first login for user {}".format(instance))

        else:
            logger.info("user logged in: {0}, last_login {1}".format(instance, old_last))
