import hashlib
from mock import patch

from django.test import override_settings, TestCase
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management import call_command

from openedx.core.djangoapps.appsembler.sites.management.commands.create_devstack_site import Command
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.theming.models import SiteTheme
from organizations.models import Organization
from provider.constants import CONFIDENTIAL
from provider.oauth2.models import AccessToken, RefreshToken, Client
from student.roles import CourseCreatorRole


@override_settings(
    DEBUG=True,
    DEFAULT_SITE_THEME='edx-theme-codebase',
    FEATURES={
        'AMC_APP_URL': 'http://localhost:13000',
        "DISABLE_COURSE_CREATION": False,
        "ENABLE_CREATOR_GROUP": True,
    },
    COMPREHENSIVE_THEME_DIRS=[settings.REPO_ROOT / 'common/test/appsembler'],
)
class CreateDevstackSiteCommandTestCase(TestCase):
    """
    Test ./manage.py lms create_devstack_site mydevstack
    """
    name = 'mydevstack'  # Used for both username, email and domain prefix.
    site_name = '{}.localhost:18000'.format(name)

    def setUp(self):
        assert settings.ENABLE_COMPREHENSIVE_THEMING
        Client.objects.create(url=settings.FEATURES['AMC_APP_URL'], client_type=CONFIDENTIAL)

    def test_no_sites(self):
        """
        Ensure nothing exists prior to the site creation.

        If something exists, it means Open edX have changed something in the sites so this
        test needs to be refactored.
        """
        assert not Site.objects.filter(domain=self.site_name).count()
        assert not Organization.objects.count()
        assert not get_user_model().objects.count()

    def test_create_devstack_site(self):
        """
        Test that `create_devstack_site` and creates the required objects.
        """
        with patch.object(Command, 'congrats') as mock_congrats:
            call_command('create_devstack_site', self.name)

        mock_congrats.assert_called_once()  # Ensure that congrats message is printed

        # Ensure objects are created correctly.
        assert Site.objects.get(domain=self.site_name)
        assert Organization.objects.get(name=self.name)
        user = get_user_model().objects.get()
        assert user.check_password(self.name)
        assert user.profile.name == self.name

        assert CourseCreatorRole().has_user(user), 'User should be a course creator'

        fake_token = hashlib.md5(user.username).hexdigest()  # Using a fake token so AMC devstack can guess it
        assert fake_token == '80bfa968ffad007c79bfc603f3670c99', 'Ensure hash is identical to AMC'
        assert AccessToken.objects.get(user=user).token == fake_token, 'Access token is needed'
        assert RefreshToken.objects.get(user=user).token == fake_token, 'Refresh token is needed'


@override_settings(
    DEBUG=True,
    DEFAULT_SITE_THEME='edx-theme-codebase',
    FEATURES={
        'AMC_APP_URL': 'http://localhost:13000',
        "DISABLE_COURSE_CREATION": False,
        "ENABLE_CREATOR_GROUP": True,
    },
    COMPREHENSIVE_THEME_DIRS=[settings.REPO_ROOT / 'common/test/appsembler'],
)
class RemoveSiteCommandTestCase(TestCase):
    """
    Test ./manage.py lms remove_site mysite
    """
    def setUp(self):
        assert settings.ENABLE_COMPREHENSIVE_THEMING
        Client.objects.create(url=settings.FEATURES['AMC_APP_URL'], client_type=CONFIDENTIAL)

        self.to_be_deleted = 'delete'
        self.shall_remain = 'keep'

        # This command should be tested above
        call_command('create_devstack_site', self.to_be_deleted)
        call_command('create_devstack_site', self.shall_remain)

    def test_create_devstack_site(self):
        """
        Test that `create_devstack_site` and creates the required objects.
        """
        call_command('remove_site', '{}.localhost:18000'.format(self.to_be_deleted))

        # Ensure objects are removed correctly.
        deleted_domain = '{}.localhost:18000'.format(self.to_be_deleted)
        remained_domain = '{}.localhost:18000'.format(self.shall_remain)

        assert not Site.objects.filter(domain=deleted_domain).exists()
        site = Site.objects.get(domain=remained_domain)

        assert SiteConfiguration.objects.count() == 1
        assert SiteConfiguration.objects.get(site=site)

        assert SiteTheme.objects.filter(site=site).count() == site.themes.count()
