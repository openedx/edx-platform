"""
utility functions for program enrollments
"""
import logging
from openedx.core.djangoapps.catalog.utils import get_programs
from organizations.models import Organization
from social_django.models import UserSocialAuth
from third_party_auth.models import SAMLProviderConfig

log = logging.getLogger(__name__)


class UserLookupException(Exception):
    pass


class ProgramDoesNotExistException(UserLookupException):
    pass


class OrganizationDoesNotExistException(UserLookupException):
    pass


class ProviderDoesNotExistException(UserLookupException):
    pass


def get_user_by_program_id(external_user_id, program_uuid):
    """
    Returns a User model for an external_user_id with a social auth entry.

    Args:
        external_user_id: external user id used for social auth
        program_uuid: a program this user is/will be enrolled in

    Returns:
        A User object or None, if no user with the given external id for the given organization exists.

    Raises:
        ProgramDoesNotExistException if no such program exists.
        OrganizationDoesNotExistException if no organization exists.
        ProviderDoesNotExistException if there is no SAML provider configured for the related organization.
    """
    program = get_programs(uuid=program_uuid)
    if program is None:
        log.error(u'Unable to find catalog program matching uuid [%s]', program_uuid)
        raise ProgramDoesNotExistException

    try:
        org_key = program['authoring_organizations'][0]['key']
        organization = Organization.objects.get(short_name=org_key)
    except (KeyError, IndexError):
        log.error(u'Cannot determine authoring organization key for catalog program [%s]', program_uuid)
        raise OrganizationDoesNotExistException
    except Organization.DoesNotExist:
        log.error(u'Unable to find organization for short_name [%s]', org_key)
        raise OrganizationDoesNotExistException

    return get_user_by_organization(external_user_id, organization)


def get_user_by_organization(external_user_id, organization):
    """
    Returns a User model for an external_user_id with a social auth entry.

    This function finds a matching SAML Provider for the given organization, and looks
    for a social auth entry with the provided exernal id.

    Args:
        external_user_id: external user id used for social auth
        organization: organization providing saml authentication for this user

    Returns:
        A User object or None, if no user with the given external id for the given organization exists.

    Raises:
        ProviderDoesNotExistException if there is no SAML provider configured for the related organization.
    """
    try:
        provider_slug = organization.samlproviderconfig_set.current_set().get().provider_id.strip('saml-')
    except SAMLProviderConfig.DoesNotExist:
        log.error(u'No SAML provider found for organization id [%s]', organization.id)
        raise ProviderDoesNotExistException
    except SAMLProviderConfig.MultipleObjectsReturned:
        log.error(
            u'Multiple active SAML configurations found for organization=%s. Expected one.',
            organization.short_name,
        )
        raise UserLookupException

    try:
        social_auth_uid = '{0}:{1}'.format(provider_slug, external_user_id)
        return UserSocialAuth.objects.get(uid=social_auth_uid).user
    except UserSocialAuth.DoesNotExist:
        return None
