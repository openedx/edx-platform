"""
This module contains signals related to enterprise.
"""

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User

from enterprise.models import EnterpriseCustomerUser
from email_marketing.tasks import update_user  # pylint: disable=import-error


@receiver(post_save, sender=EnterpriseCustomerUser)
def update_email_marketing_user_with_enterprise_flag(sender, instance, **kwargs):  # pylint: disable=unused-argument, invalid-name
    """
    Enable the is_enterprise_learner flag in SailThru vars.
    """
    user = User.objects.get(id=instance.user_id)

    # perform update asynchronously
    update_user.delay(sailthru_vars={'is_enterprise_learner': True}, email=user.email)
