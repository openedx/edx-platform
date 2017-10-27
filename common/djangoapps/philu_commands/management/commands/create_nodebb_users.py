"""
Django management command to create users at nodeBB corresponding to edx-platform users.
"""
import time
from logging import getLogger

from django.core.management.base import BaseCommand

from common.lib.nodebb_client.client import NodeBBClient
from nodebb.signals.handlers import create_user_on_nodebb
from lms.djangoapps.onboarding_survey.models import ExtendedProfile
from philu_commands.models import CreationFailedUsers

log = getLogger(__name__)


def retry(func):
    """
    A decorator which keeps on calling a function until 200 success code is returned.

    It retries the function for at most 3 times.

    Arguments:
        func(Python function): The function to retry again and again.

    returns:
        bool: True if 200 code is returned in 3 tries otherwise False.
    """
    def retry_decorator(sender, instance):
        max_retry = 3
        while max_retry >= 1:
            status_code = func(sender=sender, instance=instance)
            if not status_code:
                return False
            if status_code != 200:
                max_retry -= 1
                time.sleep(2)
                continue
            break
        if max_retry == 0:
            return False
        return True

    return retry_decorator


@retry
def create_user(sender, instance):
    """
    Creates a user on the nodeBB. We are calling a signal handler to do so.
    """
    return create_user_on_nodebb(sender=sender, instance=instance, created=True)


@retry
def activate_user(instance, **kwargs):
    """
    Activates a user on nodeBB.

    We are not using already existing signal handler here because of the mismatch
    in condition in the handler. In our case,we only need to check whether
    user is active in the edx-platform or not. If its active then activate it in
    nodeBB too.
    """
    if instance.is_active:
        status_code, response_body = NodeBBClient().users.activate(username=instance.username)
        if status_code != 200:
            log.error("Error: Can not activate user(%s) on nodebb due to %s" % (instance.username, response_body))
        else:
            log.info('Success: User(%s) has been activated on nodebb' % instance.username)

        return status_code


class Command(BaseCommand):
    help = """
    This command creates users in nodeBB according to all ExtendedProfile instances in edx-platform.

    After creating the users, it also activates them if they are active in edx-platform.
    example:
        manage.py ... create_nodebb_users
    """
    def handle(self, *args, **options):
        user_extended_profiles = ExtendedProfile.objects.all()

        for extended_profile in user_extended_profiles:
            is_created = create_user(sender=ExtendedProfile, instance=extended_profile)
            is_activated = False
            if is_created:
                is_activated = activate_user(sender=ExtendedProfile, instance=extended_profile.user)

            # If user creation or activation(or both) is failed then we make sure to record the instance
            # in the database for future reference.
            if not (is_created and is_activated):
                failed_user = CreationFailedUsers(
                    email=extended_profile.user.email, is_created=is_created, is_activated=is_activated
                )
                failed_user.save()
