"""
Django admin command to manually verify the users
"""
from logging import getLogger

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from lms.djangoapps.verify_student.models import ManualVerification


logger = getLogger(__name__)


class Command(BaseCommand):
    """
    This command attempts to manually verify users.

    Example usage:
        $ ./manage.py lms verify_all_users
    """
    help = 'Command to mark all existing users as Verified'

    def handle(self, *args, **options):
        users = User.objects.all()
        new_users_count = 0
        for user in users:
            try:
                logger.info('Generating ManualVerification for user: {}'.format(user.email))
                user, is_created = ManualVerification.objects.get_or_create(
                    user=user,
                    status='approved',
                    defaults={
                        'name': user.profile.name,
                        'reason': 'SKIP_IDENTITY_VERIFICATION',
                    }
                )
                if is_created:
                    new_users_count += 1

            except Exception:  # pylint: disable=broad-except
                logger.error('Error while generating ManualVerification for user: %s', user.email, exc_info=True)

        logger.info('{} new user(s) have been verified'.format(new_users_count))
