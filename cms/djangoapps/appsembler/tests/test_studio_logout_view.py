"""
Tests for APPSEMBLER_MULTI_TENANT_EMAILS in Studio logout.

Special note:

This test module needs to patch `cms.urls.urlpatterns` to include urlpatterns
from `cms.djangoapps.appsembler.urls`. This works by overriding the
`doango.conf.settings.ROOT_URLCONF` with `django.test.utils.override_settings`
at the TestCase class level with the `urlpatterns` list declared in the module
containing the TestCase class.

For this test module, we've added a `urlpatterns` module level variable and
assigned it the value of `cms.urls.urlpatterns` then appended the conditionally
included urlpatterns we need to run the tests.

Then we add `@override_settings(ROOT_URLCONF=__name__)` to the TestClass

There are other ways to do this. However, this is simple and does not require
our code to explicitly hack `sys.modules` reloading
"""
from unittest.mock import Mock, patch

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import auth
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from rest_framework import status
from tahoe_sites.api import add_user_to_organization, create_tahoe_site

from student.tests.factories import UserFactory
import cms.urls
from cms.djangoapps.appsembler.views import get_logout_redirect_url


# Set the urlpatterns we want to use for our tests in this module only
urlpatterns = cms.urls.urlpatterns + [
    url(r'', include('cms.djangoapps.appsembler.urls'))
]


@override_settings(ROOT_URLCONF=__name__)  # the module that contains `urlpatterns`
@override_settings(LOGOUT_REDIRECT_URL='home')  # ensure that we have a value for LOGOUT_REDIRECT_URL
@patch.dict('django.conf.settings.FEATURES', {'TAHOE_STUDIO_LOCAL_LOGIN': True})
class TestStudioLogoutView(TestCase):
    """
    Testing the APPSEMBLER_MULTI_TENANT_EMAILS feature when enabled in Studio.
    """
    BLUE = 'blue1'
    EMAIL = 'customer@example.com'
    PASSWORD = 'xyz'
    DOMAIN = 'testdomain.com'
    SHORT_NAME = 'testdomain'

    def setUp(self):
        super(TestStudioLogoutView, self).setUp()
        self.url = reverse('logout')
        self.user = UserFactory.create(email=self.EMAIL, password=self.PASSWORD)
        add_user_to_organization(
            user=self.user,
            organization=create_tahoe_site(domain=self.DOMAIN, short_name=self.SHORT_NAME)['organization']
        )
        self.request = RequestFactory()
        self.request.is_secure = Mock(return_value=False)
        self.lms_url = 'http://{site_domain}/logout'.format(site_domain=self.DOMAIN)

    def test_logout_must_be_authenticated(self):
        """
        Test logout from studio must be authenticated
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_302_FOUND
        assert not response.content
        assert '?next=/logout' in response.url

    def test_logout_normal_user(self):
        """
        Test logout from studio for normal users (meaning that they are linked to an organization). It is expected
        that a logout then redirect to LMS will be performed
        """
        self.client.login(username=self.user.username, password=self.PASSWORD)
        assert auth.get_user(self.client).is_authenticated

        response = self.client.get(self.url)
        assert not auth.get_user(self.client).is_authenticated

        assert response.status_code == status.HTTP_302_FOUND
        assert not response.content
        assert response.url == self.lms_url

    def test_logout_staff_user(self):
        """
        Test logout from studio for staff users (meaning that they are not linked to any organization). It is expected
        that a logout then a redirect to settings.LOGOUT_REDIRECT_URL will be performed
        """
        # Not necessary to set the user as staff, the thing we need to test is when it lacks a link to an organization
        user = UserFactory.create(email=self.EMAIL, password=self.PASSWORD)

        self.client.login(username=user.username, password=self.PASSWORD)
        assert auth.get_user(self.client).is_authenticated

        response = self.client.get(self.url)
        assert not auth.get_user(self.client).is_authenticated

        assert response.status_code == status.HTTP_302_FOUND
        assert not response.content
        assert response.url == reverse(settings.LOGOUT_REDIRECT_URL)

    def test_get_logout_redirect_url_no_request(self):
        """
        Verify that get_logout_redirect_url will return settings.LOGOUT_REDIRECT_URL if the request is None
        """
        assert get_logout_redirect_url(request=None) == reverse(settings.LOGOUT_REDIRECT_URL)

    def test_get_logout_redirect_url_no_user(self):
        """
        Verify that get_logout_redirect_url will return settings.LOGOUT_REDIRECT_URL if no user is logged in
        """
        assert not hasattr(self.request, 'user')
        assert get_logout_redirect_url(request=self.request) == reverse(settings.LOGOUT_REDIRECT_URL)

    def test_get_logout_redirect_url_anonymous(self):
        """
        Verify that get_logout_redirect_url will return settings.LOGOUT_REDIRECT_URL if the user is anonymous
        """
        self.request.user = AnonymousUser()
        assert get_logout_redirect_url(request=self.request) == reverse(settings.LOGOUT_REDIRECT_URL)

    def test_get_logout_redirect_url_user(self):
        """
        Verify that get_logout_redirect_url will return the LMS URL related to the user
        """
        self.request.user = self.user
        assert get_logout_redirect_url(request=self.request) == self.lms_url

    def test_get_logout_redirect_url_staff(self):
        """
        Verify that get_logout_redirect_url will return settings.LOGOUT_REDIRECT_URL if the user is not linked to
        any organization (staff users and superusers)
        """
        user = UserFactory.create(email=self.EMAIL, password=self.PASSWORD)
        self.request.user = user
        assert get_logout_redirect_url(request=self.request) == reverse(settings.LOGOUT_REDIRECT_URL)
