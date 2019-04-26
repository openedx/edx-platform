"""
This module contains signals related to enterprise.
"""

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User

from enterprise.models import EnterpriseCustomerUser, EnterpriseCourseEnrollment
from email_marketing.tasks import update_user

from openedx.features.enterprise_support.utils import clear_data_consent_share_cache


@receiver(post_save, sender=EnterpriseCustomerUser)
def update_email_marketing_user_with_enterprise_vars(sender, instance, **kwargs):  # pylint: disable=unused-argument, invalid-name
    """
    Update the SailThru user with enterprise-related vars.
    """
    user = User.objects.get(id=instance.user_id)

    # perform update asynchronously
    update_user.delay(
        sailthru_vars={
            'is_enterprise_learner': True,
            'enterprise_name': instance.enterprise_customer.name,
        },
        email=user.email
    )


@receiver(post_save, sender=EnterpriseCourseEnrollment)
def update_data_consent_share_cache(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
        clears data_sharing_consent_needed cache after Enterprise Course Enrollment
    """
    clear_data_consent_share_cache(
        instance.enterprise_customer_user.user_id,
        instance.course_id
    )
