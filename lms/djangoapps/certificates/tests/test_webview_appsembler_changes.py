"""
Test changes we've done to the `webview` internal helpers.
"""

from mock import patch, Mock
from django.test import TestCase

from lms.djangoapps.certificates.views.webview import _update_organization_context  # pylint: disable=protected-access


@patch(
    'util.organizations_helpers.get_course_organizations',
    Mock(return_value=[{
        # List of a single organization.
        'name': 'org-name',
        'short_name': 'org-name',
        'logo': None,
    }])
)
class UpdateOrganizationContextTestCase(TestCase):
    """
    Tests for the `_update_organization_context` function.
    """

    def test_without_course_org_name_override(self):
        """
        Ensure `partner_short_name_overridden` is properly set to False by default.
        """
        context = {}
        course = Mock()
        course.display_organization = None  # Not overridden
        course.org = 'org-name'

        _update_organization_context(context, course)

        assert not context['partner_short_name_overridden'], 'Should be set to False so certs work properly'
        assert context['course_partner_short_name'] == 'org-name'

    def test_with_course_org_name_override(self):
        context = {}
        course = Mock()
        course.org = 'org-name'
        course.display_organization = 'Custom Org Name'  # Not overridden

        _update_organization_context(context, course)

        assert context['partner_short_name_overridden'], 'Should be set to True so certs work properly'
        assert context['course_partner_short_name'] == 'Custom Org Name'
