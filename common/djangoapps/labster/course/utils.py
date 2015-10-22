""" Labster Course utils. """
import logging

from django.contrib.auth.models import User
from contentstore.utils import add_instructor, remove_all_instructors


log = logging.getLogger(__name__)


def set_staff(course_key, emails):
    """
    Sets course staff.
    """
    remove_all_instructors(course_key)
    for email in emails:
        try:
            user = User.objects.get(email=email)
            add_instructor(course_key, user, user)
        except User.DoesNotExist:
            log.info('User with email %s does not exist', email)
