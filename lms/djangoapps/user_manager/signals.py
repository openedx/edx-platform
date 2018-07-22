"""
Signals for User Manager app
"""
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from lms.djangoapps.user_manager.models import UserManagerRole


@receiver(post_save, sender=User)
def upgrade_manager_role_entry(sender, **kwargs):  # pylint: disable=unused-argument
    """
    """
    created = kwargs.get('created')
    user = kwargs.get('instance')

    if created and user:
        UserManagerRole.objects.filter(
            unregistered_manager_email=user.email
        ).update(
            unregistered_manager_email=None,
            manager_user=user,
        )

