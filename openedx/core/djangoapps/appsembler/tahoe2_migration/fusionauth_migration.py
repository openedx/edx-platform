"""
Migrate the users to FusionAuth.
"""
import base64

import uuid
from logging import getLogger

from fusionauth.fusionauth_client import FusionAuthClient
import tahoe_sites.api
from django.conf import settings
from social_django.models import UserSocialAuth
from tahoe_idp.permissions import METADATE_ROLE_FIELD

from openedx.core.djangoapps.appsembler.tahoe_idp.constants import TAHOE_IDP_BACKEND_NAME


log = getLogger(__name__)


def get_fa_api_client(fusionauth_tenant_id):
    """
    Get a configured Rest API client for the Identity Provider.
    """
    client = FusionAuthClient(
        api_key=settings.TAHOE_IDP_CONFIGS['API_KEY'],
        base_url=settings.TAHOE_IDP_CONFIGS['BASE_URL'],
    )
    client.set_tenant_id(fusionauth_tenant_id)
    return client


def read_password(user):
    """
    Adapted from django.contrib.auth.hashers module.
    """
    password = user.password
    algorithm, factor, salt, hash_b64 = password.split('$', 3)
    assert algorithm == 'pbkdf2_sha256', 'User {} has a unknown hashing algorithm {}'.format(user, algorithm)
    return {
        'factor': int(factor),  # Hashing iterations
        'salt_b64_str': base64.b64encode(salt.encode('utf-8')).decode('utf-8'),
        'hash_b64_str': hash_b64,
    }


def migrate_user_to_fa(user, organization, api_client):
    if not user.is_active:
        log.warning('skipped inactive user %s %s', user.id, user)
        return

    if user.is_staff or user.is_superuser:
        log.warning('skipped staff user %s %s', user.id, user)
        return

    if tahoe_sites.api.is_active_admin_on_organization(user=user, organization=organization):
        role = 'Administrator'
    else:
        role = 'Learner'

    password = read_password(user)

    new_fusion_auth_user_uuid = str(uuid.uuid4())  # Security: This should generate a secure random UUID
    encryption_scheme = 'salted-pbkdf2-hmac-sha256'  # FusionAuth equivalent of Django 2.22 pbkdf2_sha256
    users_data = {
        'validateDbConstraints': True,
        'users': [{
            'id': new_fusion_auth_user_uuid,
            'active': user.is_active,
            'verified': user.is_active,
            'email': user.email,
            'fullName': user.profile.name,
            'username': user.username,

            'encryptionScheme': encryption_scheme,
            'factor': password['factor'],
            'salt': password['salt_b64_str'],
            'password': password['hash_b64_str'],

            'data': {
                METADATE_ROLE_FIELD: role,
                'tahoe_user_id': user.id,
                'tahoe_user_last_login': str(user.last_login.date()),
                'tahoe_user_date_joined': str(user.date_joined.date())
            }
        }]
    }
    resp = api_client.import_users(users_data)
    assert resp.was_successful(), 'Failed to import user: {}'.format(resp.response.content.decode('utf-8'))

    UserSocialAuth.objects.create(
        user=user, provider=TAHOE_IDP_BACKEND_NAME, uid=new_fusion_auth_user_uuid,
    )
