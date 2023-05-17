"""
Tests for Edly Course Enrollment ViewSet.
"""
from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.conf import settings

from student.tests.factories import GroupFactory, UserFactory

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.features.edly.tests.factories import EdlySubOrganizationFactory


class TestEdlyCourseEnrollmentViewSett(TestCase):
    """
    Tests for "UserSitesViewSet".
    """

    def setUp(self):
        """
        Setup initial test data
        """
        super(TestEdlyCourseEnrollmentViewSett, self).setUp()
        self.request_site = SiteFactory()
        self.edly_sub_org = EdlySubOrganizationFactory(
            lms_site=self.request_site,
            studio_site=self.request_site,
            preview_site=self.request_site,
            )
        self.request = RequestFactory(SERVER_NAME=self.request_site.domain).get('')
        self.request.site = self.request_site
        self.user = UserFactory(is_staff=True, is_superuser=True, edly_multisite_user__sub_org=self.edly_sub_org)
        self.request.user = self.user
        self.client = Client(SERVER_NAME=self.request_site.domain)
        self.client.login(username=self.user.username, password='test')
        self.course_enrollments_url = reverse('course_enrollment-list')

    def test_with_logged_in_non_edly_api_group_user(self):
        """
        Verify that returns correct response if user not in edly_api_users_group.
        """
        response = self.client.get(self.course_enrollments_url)

        assert response.status_code == 403

    def test_with_logged_in_edly_api_group_user(self):
        """
        Verify that returns correct response if user logged in and in edly_api_users_group.
        """
        edly_api_users_group = GroupFactory(name=settings.EDLY_API_USERS_GROUP)
        self.user.edly_multisite_user.get(sub_org=self.edly_sub_org).groups.add(edly_api_users_group)  # pylint:disable=E1101
        self.client.login(username=self.user.username, password='test')
        response = self.client.get(self.course_enrollments_url)

        assert response.status_code == 200

    def test_list_without_logged_in_user(self):
        """
        Verify that returns correct response when user is not logged in.
        """
        self.client.logout()
        response = self.client.get(self.course_enrollments_url)

        assert response.status_code == 401
