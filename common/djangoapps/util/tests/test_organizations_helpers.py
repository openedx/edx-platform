"""
Tests for the organizations helpers library, which is the integration point for the edx-organizations API
"""
from mock import patch

from util import organizations_helpers
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@patch.dict('django.conf.settings.FEATURES', {'ORGANIZATIONS_APP': False})
class OrganizationsHelpersTestCase(ModuleStoreTestCase):
    """
    Main test suite for Organizations API client library
    """

    def setUp(self):
        """
        Test case scaffolding
        """
        super(OrganizationsHelpersTestCase, self).setUp(create_user=False)
        self.course = CourseFactory.create()

        self.organization = {
            'name': 'Test Organization',
            'short_name': 'Orgx',
            'description': 'Testing Organization Helpers Library',
        }

    def test_get_organization_returns_none_when_app_disabled(self):
        response = organizations_helpers.get_organization(1)
        self.assertEqual(len(response), 0)

    def test_get_organizations_returns_none_when_app_disabled(self):
        response = organizations_helpers.get_organizations()
        self.assertEqual(len(response), 0)

    def test_get_organization_courses_returns_none_when_app_disabled(self):
        response = organizations_helpers.get_organization_courses(1)
        self.assertEqual(len(response), 0)

    def test_get_course_organizations_returns_none_when_app_disabled(self):
        response = organizations_helpers.get_course_organizations(unicode(self.course.id))
        self.assertEqual(len(response), 0)

    def test_add_organization_returns_none_when_app_disabled(self):
        response = organizations_helpers.add_organization(organization_data=self.organization)
        self.assertIsNone(response)

    def test_add_organization_course_returns_none_when_app_disabled(self):
        response = organizations_helpers.add_organization_course(self.organization, self.course.id)
        self.assertIsNone(response)

    def test_get_organization_by_short_name_when_app_disabled(self):
        """
        Tests get_organization_by_short_name api when app is disabled.
        """
        response = organizations_helpers.get_organization_by_short_name(self.organization['short_name'])
        self.assertIsNone(response)

    @patch.dict('django.conf.settings.FEATURES', {'ORGANIZATIONS_APP': True})
    def test_get_organization_by_short_name_when_app_enabled(self):
        """
        Tests get_organization_by_short_name api when app is enabled.
        """
        response = organizations_helpers.add_organization(organization_data=self.organization)
        self.assertIsNotNone(response['id'])

        response = organizations_helpers.get_organization_by_short_name(self.organization['short_name'])
        self.assertIsNotNone(response['id'])

        # fetch non existing org
        response = organizations_helpers.get_organization_by_short_name('non_existing')
        self.assertIsNone(response)
