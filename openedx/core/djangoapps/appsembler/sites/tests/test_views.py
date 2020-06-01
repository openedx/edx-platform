"""
Tests for the Apppsembler API views.
"""
from mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.core.djangoapps.appsembler.multi_tenant_emails.tests.test_utils import (
    with_organization_context,
    create_org_user,
)


@skip_unless_lms
@patch(
    # Skip AMC API key check
    'openedx.core.djangoapps.appsembler.sites.api.FindUsernameByEmailView.permission_classes', []
)
class TestFindUsernameByEmailView(APITestCase):
    """
    Tests for the FindUsernameOnOrg view.
    """

    def setUp(self):
        super(TestFindUsernameByEmailView, self).setUp()
        self.url = reverse('tahoe_find_username_by_email')

    def get_username(self, email, organization_name):
        """
        Fetch username via the FindUsernameOnOrg view.
        """
        return self.client.get(self.url, {
            'email': email,
            'organization_name': organization_name,
        })

    def test_find_username(self):
        """
        Test happy scenario.
        """
        email = 'learner@red.org'
        username = 'learner_xyz'
        with with_organization_context(site_color='red1') as red_org:
            create_org_user(red_org, email=email, username=username)

        response = self.get_username(email, red_org.name)
        assert response.status_code == status.HTTP_200_OK, response.content
        assert response.json()['username'] == username

    def test_organization_separation(self):
        """
        Test organization collision.
        """
        color1 = 'red1'
        email = 'learner@red.org'
        username = 'learner_xyz'
        with with_organization_context(site_color=color1) as red_org:
            create_org_user(red_org, email=email, username=username)

        with with_organization_context(site_color='blue1') as blue_org:
            pass

        response = self.get_username(email, blue_org.name)
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.content  # Should keep sites separated

        blue_user = create_org_user(blue_org, email=email)
        response = self.get_username(email, blue_org.name)
        assert response.status_code == status.HTTP_200_OK, response.content
        assert response.json()['username'] == blue_user.username

    def test_not_found(self):
        """
        Test missing email.
        """
        with with_organization_context(site_color='empty_org') as red_org:
            pass

        response = self.get_username('nobody@example.com', red_org.name)
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.content
