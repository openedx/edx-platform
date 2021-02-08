"""
Django management command to create users at nodeBB corresponding to edx-platform users.
"""
import time
from logging import getLogger

from django.core.management.base import BaseCommand
from requests.exceptions import ConnectionError

from nodebb.tasks import (
    task_create_user_on_nodebb,
    task_activate_user_on_nodebb,
    task_update_user_profile_on_nodebb,
    task_update_onboarding_surveys_status
)
from common.lib.nodebb_client.client import NodeBBClient
from lms.djangoapps.onboarding.helpers import COUNTRIES
from lms.djangoapps.onboarding.models import UserExtendedProfile
from philu_commands.models import CreationFailedUsers

log = getLogger(__name__)


class Command(BaseCommand):
    help = """
    This command creates users in nodeBB according to all UserExtendedProfile instances in edx-platform.

    After creating the users, it also activates them if they are active in edx-platform.
    example:
        manage.py ... create_nodebb_users
    """

    def handle(self, *args, **options):
        user_extended_profiles = UserExtendedProfile.objects.all()
        nodebb_client = NodeBBClient()

        status_code, nodebb_users = nodebb_client.users.all()  # returns tuple of (status_code, response_body)
        if status_code != 200:
            log.error('Error: failed to connect to NodeBB. aborting command "{}"'.format('sync_users_with_nodebb'))
            return

        nodebb_users = {user['username']: user for user in nodebb_users}

        for extended_profile in user_extended_profiles:
            user = extended_profile.user
            profile = user.profile

            edx_data = {
                'edx_user_id': unicode(user.id),
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'country_of_employment': extended_profile.country_of_employment,
                'city_of_employment': extended_profile.city_of_employment,
                'country_of_residence': COUNTRIES.get(profile.country.code),
                'city_of_residence': profile.city,
                'birthday': profile.year_of_birth,
                'language': profile.language,
                'interests': extended_profile.get_user_selected_interests(),
                'self_prioritize_areas': extended_profile.get_user_selected_functions()
            }

            nodebb_data = nodebb_users.get(user.username)

            if not nodebb_data:
                task_create_user_on_nodebb.delay(username=user.username, user_data=edx_data)
                if user.is_active:
                    task_activate_user_on_nodebb.delay(username=user.username, active=user.is_active)
                # if user has submitted all onboarding surveys then update status on NodeBB
                if not bool(extended_profile.unattended_surveys(_type='list')):
                    task_update_onboarding_surveys_status.delay(username=user.username)
                continue

            # filter nodebb_data to ensure compatibility with edx_data
            for key in nodebb_data:
                if unicode(nodebb_data[key]) == u'None':
                    nodebb_data[key] = None
            if not nodebb_data.get('self_prioritize_areas'):
                nodebb_data['self_prioritize_areas'] = []

            if not edx_data.viewitems() <= nodebb_data.viewitems():
                task_update_user_profile_on_nodebb.delay(username=user.username, profile_data=edx_data)
