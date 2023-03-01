"""
Management command to generate Transfer Identifiers for users who signed in with Apple.
These transfer identifiers are used in the event of migrating an app from one team to another.
"""


import logging
import requests
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import jwt
from social_django.models import UserSocialAuth
from social_django.utils import load_strategy


from common.djangoapps.third_party_auth.models import AppleMigrationUserIdInfo
from common.djangoapps.third_party_auth.appleid import AppleIdAuth

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to generate transfer identifiers for apple users using their apple_id
    stored in social_django.models.UserSocialAuth.uid.

    Usage:
        manage.py generate_and_store_apple_transfer_ids <target_team_id>
    """

    def _generate_client_secret(self):
        """
        Generate client secret for use in Apple API's
        """
        now = int(time.time())
        expiry = 60 * 60 * 3  # 3 hours

        backend = load_strategy().get_backend(AppleIdAuth.name)
        team_id = backend.setting('TEAM')
        key_id = backend.setting('KEY')
        private_key = backend.get_private_key()
        audience = backend.TOKEN_AUDIENCE

        headers = {
            "alg": "ES256",
            'kid': key_id
        }
        payload = {
            'iss': team_id,
            'iat': now,
            'exp': now + expiry,
            'aud': audience,
            'sub': "org.edx.mobile",
        }

        return jwt.encode(payload, key=private_key, algorithm='ES256',
                          headers=headers)

    def _generate_access_token(self, client_secret):
        """
        Generate access token for use in Apple API's
        """
        access_token_url = 'https://appleid.apple.com/auth/token'
        app_id = "org.edx.mobile"
        payload = {
            "grant_type": "client_credentials",
            "scope": "user.migration",
            "client_id": app_id,
            "client_secret": client_secret
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "appleid.apple.com"
        }
        response = requests.post(access_token_url, data=payload, headers=headers)
        access_token = response.json().get('access_token')
        return access_token

    def add_arguments(self, parser):
        parser.add_argument('target_team_id', help='Team ID to which the app is to be migrated to.')

    @transaction.atomic
    def handle(self, *args, **options):
        target_team_id = options['target_team_id']

        migration_url = "https://appleid.apple.com/auth/usermigrationinfo"
        app_id = "org.edx.mobile"

        client_secret = self._generate_client_secret()
        access_token = self._generate_access_token(client_secret)
        if not access_token:
            raise CommandError('Failed to create access token.')

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "appleid.apple.com",
            "Authorization": "Bearer " + access_token
        }
        payload = {
            "target": target_team_id,
            "client_id": app_id,
            "client_secret": client_secret
        }

        apple_ids = UserSocialAuth.objects.filter(provider=AppleIdAuth.name).values_list('uid', flat=True)
        print(apple_ids)
        print(AppleIdAuth.name)
        for apple_id in apple_ids:
            payload['sub'] = apple_id
            response = requests.post(migration_url, data=payload, headers=headers)
            transfer_id = response.json().get('transfer_sub')
            if transfer_id:
                apple_user_id_info, _ = AppleMigrationUserIdInfo.objects.get_or_create(old_apple_id=apple_id)
                apple_user_id_info.transfer_id = transfer_id
                apple_user_id_info.save()
                log.info('Updated transfer_id for uid %s', apple_id)
            else:
                log.info('Unable to fetch transfer_id for uid %s', apple_id)
