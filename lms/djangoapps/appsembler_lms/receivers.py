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
        if not old_last:
            logger.info("First time login for user {}".format(instance))
            # ping AMC

        else:
            logger.info("user logged in: {0}, last_login {1}".format(instance, old_last))
