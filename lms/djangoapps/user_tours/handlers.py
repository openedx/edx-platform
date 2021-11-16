""" Signal handlers for User Tours. """

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from lms.djangoapps.user_tours.models import UserTour

User = get_user_model()


@receiver(post_save, sender=User)
def init_user_tour(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    """
    Initialize a new User Tour when a new user is created.
    """
    if created:
        UserTour.objects.create(user=instance)
