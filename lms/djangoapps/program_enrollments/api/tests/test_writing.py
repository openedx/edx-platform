"""
Tests for program enrollment writing Python API.

Currently, we do not directly unit test the functions in api/writing.py extensively.
This is okay for now because they are all used in
`rest_api.v1.views` and is thus tested through `rest_api.v1.tests.test_views`.
Eventually it would be good to directly test the Python API function and just use
mocks in the view tests.
"""
from __future__ import absolute_import, unicode_literals

from uuid import UUID

from organizations.tests.factories import OrganizationFactory
from django.core.cache import cache

from lms.djangoapps.program_enrollments.constants import ProgramEnrollmentStatuses as PEStatuses
from lms.djangoapps.program_enrollments.models import ProgramEnrollment
from openedx.core.djangoapps.catalog.cache import PROGRAM_CACHE_KEY_TPL
from openedx.core.djangoapps.catalog.tests.factories import OrganizationFactory as CatalogOrganizationFactory
from openedx.core.djangoapps.catalog.tests.factories import ProgramFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from third_party_auth.tests.factories import SAMLProviderConfigFactory

from ..writing import (
    write_program_enrollments
)


class WritingProgramEnrollmentTest(CacheIsolationTestCase):
    """
    Test cases for program enrollment writing functions.
    """
    ENABLED_CACHES = ['default']

    organization_key = 'test'

    program_uuid_x = UUID('dddddddd-5f48-493d-9910-84e1d36c657f')

    curriculum_uuid_a = UUID('aaaaaaaa-bd26-4370-94b8-b4063858210b')

    user_0 = 'user-0'

    def setUp(self):
        """
        Set up test data
        """
        super(WritingProgramEnrollmentTest, self).setUp()
        catalog_org = CatalogOrganizationFactory.create(key=self.organization_key)
        program = ProgramFactory.create(
            uuid=self.program_uuid_x,
            authoring_organizations=[catalog_org]
        )
        organization = OrganizationFactory.create(short_name=self.organization_key)
        SAMLProviderConfigFactory.create(organization=organization)
        cache.set(PROGRAM_CACHE_KEY_TPL.format(uuid=self.program_uuid_x), program, None)

    def test_write_program_enrollments_status_ended(self):
        """
        Successfully updates program enrollment to status ended if requested
        """
        assert ProgramEnrollment.objects.count() == 0
        write_program_enrollments(self.program_uuid_x, [{
            'external_user_key': self.user_0,
            'status': PEStatuses.PENDING,
            'curriculum_uuid': self.curriculum_uuid_a,
        }], True, False)
        assert ProgramEnrollment.objects.count() == 1
        write_program_enrollments(self.program_uuid_x, [{
            'external_user_key': self.user_0,
            'status': PEStatuses.ENDED,
            'curriculum_uuid': self.curriculum_uuid_a,
        }], False, True)
        assert ProgramEnrollment.objects.count() == 1
        assert ProgramEnrollment.objects.filter(status=PEStatuses.ENDED).exists()
