"""
Unit tests for program_enrollments utils.
"""
from __future__ import absolute_import

from uuid import uuid4

import pytest
from django.core.cache import cache
from organizations.tests.factories import OrganizationFactory
from social_django.models import UserSocialAuth

from openedx.core.djangoapps.catalog.cache import PROGRAM_CACHE_KEY_TPL
from openedx.core.djangoapps.catalog.tests.factories import OrganizationFactory as CatalogOrganizationFactory
from openedx.core.djangoapps.catalog.tests.factories import ProgramFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from program_enrollments.utils import (
    OrganizationDoesNotExistException,
    ProgramDoesNotExistException,
    ProviderDoesNotExistException,
    get_user_by_program_id
)
from student.tests.factories import UserFactory
from third_party_auth.tests.factories import SAMLProviderConfigFactory


class GetPlatformUserTests(CacheIsolationTestCase):
    """
    Tests for the get_platform_user function
    """
    ENABLED_CACHES = ['default']

    def setUp(self):
        super(GetPlatformUserTests, self).setUp()
        self.program_uuid = uuid4()
        self.organization_key = 'ufo'
        self.external_user_id = '1234'
        self.user = UserFactory.create()
        self.setup_catalog_cache(self.program_uuid, self.organization_key)

    def setup_catalog_cache(self, program_uuid, organization_key):
        """
        helper function to initialize a cached program with an single authoring_organization
        """
        catalog_org = CatalogOrganizationFactory.create(key=organization_key)
        program = ProgramFactory.create(
            uuid=program_uuid,
            authoring_organizations=[catalog_org]
        )
        cache.set(PROGRAM_CACHE_KEY_TPL.format(uuid=program_uuid), program, None)

    def create_social_auth_entry(self, user, provider, external_id):
        """
        helper functio to create a user social auth entry
        """
        UserSocialAuth.objects.create(
            user=user,
            uid='{0}:{1}'.format(provider.slug, external_id)
        )

    def test_get_user_success(self):
        """
        Test lms user is successfully found
        """
        organization = OrganizationFactory.create(short_name=self.organization_key)
        provider = SAMLProviderConfigFactory.create(organization=organization)
        self.create_social_auth_entry(self.user, provider, self.external_user_id)

        user = get_user_by_program_id(self.external_user_id, self.program_uuid)
        self.assertEquals(user, self.user)

    def test_social_auth_user_not_created(self):
        """
        None should be returned if no lms user exists for an external id
        """
        organization = OrganizationFactory.create(short_name=self.organization_key)
        SAMLProviderConfigFactory.create(organization=organization)

        user = get_user_by_program_id(self.external_user_id, self.program_uuid)
        self.assertIsNone(user)

    def test_catalog_program_does_not_exist(self):
        """
        Test ProgramDoesNotExistException is thrown if the program cache does
        not include the requested program uuid.
        """
        with pytest.raises(ProgramDoesNotExistException):
            get_user_by_program_id('school-id-1234', uuid4())

    def test_catalog_program_missing_org(self):
        """
        Test OrganizationDoesNotExistException is thrown if the cached program does not
        have an authoring organization.
        """
        program = ProgramFactory.create(
            uuid=self.program_uuid,
            authoring_organizations=[]
        )
        cache.set(PROGRAM_CACHE_KEY_TPL.format(uuid=self.program_uuid), program, None)

        organization = OrganizationFactory.create(short_name=self.organization_key)
        provider = SAMLProviderConfigFactory.create(organization=organization)
        self.create_social_auth_entry(self.user, provider, self.external_user_id)

        with pytest.raises(OrganizationDoesNotExistException):
            get_user_by_program_id(self.external_user_id, self.program_uuid)

    def test_lms_organization_not_found(self):
        """
        Test an OrganizationDoesNotExistException is thrown if the LMS has no organization
        matching the catalog program's authoring_organization
        """
        organization = OrganizationFactory.create(short_name='some_other_org')
        provider = SAMLProviderConfigFactory.create(organization=organization)
        self.create_social_auth_entry(self.user, provider, self.external_user_id)

        with pytest.raises(OrganizationDoesNotExistException):
            get_user_by_program_id(self.external_user_id, self.program_uuid)

    def test_saml_provider_not_found(self):
        """
        Test an sdf is thrown if no SAML provider exists for this program's organization
        """
        OrganizationFactory.create(short_name=self.organization_key)

        with pytest.raises(ProviderDoesNotExistException):
            get_user_by_program_id(self.external_user_id, self.program_uuid)
