import hashlib
import pkg_resources
from mock import patch, mock_open
from StringIO import StringIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from openedx.core.djangoapps.appsembler.sites.management.commands.create_devstack_site import Command
from openedx.core.djangoapps.appsembler.sites.management.commands.export_site import Command as ExportSiteCommand
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.theming.models import SiteTheme
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings, TestCase

from organizations.models import Organization
from provider.constants import CONFIDENTIAL
from provider.oauth2.models import AccessToken, RefreshToken, Client
from student.roles import CourseCreatorRole


@override_settings(
    DEBUG=True,
    DEFAULT_SITE_THEME='edx-theme-codebase',
)
@patch.dict('django.conf.settings.FEATURES', {
    'DISABLE_COURSE_CREATION': False,
    'ENABLE_CREATOR_GROUP': True,
})
class CreateDevstackSiteCommandTestCase(TestCase):
    """
    Test ./manage.py lms create_devstack_site mydevstack
    """
    name = 'mydevstack'  # Used for both username, email and domain prefix.
    site_name = '{}.localhost:18000'.format(name)

    def setUp(self):
        assert settings.ENABLE_COMPREHENSIVE_THEMING
        Client.objects.create(url=settings.AMC_APP_URL, client_type=CONFIDENTIAL)

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
)
@patch.dict('django.conf.settings.FEATURES', {
    'DISABLE_COURSE_CREATION': False,
    'ENABLE_CREATOR_GROUP': True,
})
class RemoveSiteCommandTestCase(TestCase):
    """
    Test ./manage.py lms remove_site mysite
    """
    def setUp(self):
        assert settings.ENABLE_COMPREHENSIVE_THEMING
        Client.objects.create(url=settings.AMC_APP_URL, client_type=CONFIDENTIAL)

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


class TestExportSiteCommand(TestCase):
    """
    Test ./manage.py lms export_site somesite
    """

    def setUp(self):
        self.site_name = 'site'
        self.site_domain = '{}.localhost:18000'.format(self.site_name)
        self.site = Site.objects.create(domain=self.site_domain, name=self.site_name)

        self.command = ExportSiteCommand()

    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.export_site.Command.get_pip_packages', return_value={})
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.export_site.Command.write_to_file', return_value='called')
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.export_site.Command.check')
    def test_handle(self, mock_check, mock_write_to_file, mock_get_pip_packages):
        out = StringIO()
        call_command('export_site', self.site_domain, stdout=out)

        assert mock_check.called
        assert mock_get_pip_packages.called
        assert mock_write_to_file.called

        assert 'Exporting "%s" in progress' % self.site_domain in out.getvalue()
        assert 'Successfully exported' in out.getvalue()
        assert 'Command output >>>' not in out.getvalue()

    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.export_site.Command.get_pip_packages', return_value={})
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.export_site.Command.write_to_file', return_value='called')
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.export_site.Command.check')
    def test_handle_debug(self, mock_check, mock_write_to_file, mock_get_pip_packages):
        out = StringIO()
        call_command('export_site', self.site_domain, debug=True, stdout=out)

        assert mock_check.called
        assert mock_get_pip_packages.called
        assert mock_write_to_file.called

        assert 'Exporting "%s" in progress' % self.site_domain in out.getvalue()
        assert 'Command output >>>' in out.getvalue()
        assert 'Successfully exported' in out.getvalue()

    def test_handle_system_check_fails(self):
        """
        According to Django, serious problems are raised as a CommandError wheb calling
        this `check` function. Proccessing should stop in case we got a serious problem.

        https://docs.djangoproject.com/en/1.11/howto/custom-management-commands/#django.core.management.BaseCommand.check
        """

        with patch('openedx.core.djangoapps.appsembler.sites.management.commands.export_site.Command.check', side_effect=CommandError()):
            with self.assertRaises(CommandError):
                call_command('export_site', self.site_domain, debug=True)
            with self.assertRaises(CommandError):
                call_command('export_site', self.site_domain)

    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.export_site.Command.process_instance')
    def test_generate_objects_bfs(self, mock_process_instance):
        """
        To be able to test BFS we need a graph structure, this mimics database
        relations to some extent.
        """
        mock_process_instance.side_effect = self.fake_process_instance
        objects = self.command.generate_objects('microsite')

        # Each assert is a level where its elements can be exchangeble.
        assert objects[0] == 'microsite'
        assert objects[1] == 'organization_1'
        assert set(objects[2:5]) == {'user_1', 'user_2', 'tier'}
        assert set(objects[5:8]) == {'user_terms_conditions_1', 'auth_token_1', 'user_terms_conditions_2'}
        assert objects[8] == 'auth_token_2'
        assert set(objects[9:]) == {'terms_1', 'terms_2'}

    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.export_site.Command.process_instance')
    def test_generate_objects_integrity(self, mock_process_instance):
        """
        makes sure that:
            - All required objects are processed.
            - Unrelated objects are not included.
            - No object appears more than once.
        """
        mock_process_instance.side_effect = self.fake_process_instance
        objects = self.command.generate_objects('microsite')

        # Test duplicates
        assert len(objects) == len(set(objects))

        # Test exact items
        assert set(objects) == {
            'microsite',
            'organization_1',
            'user_1',
            'user_2',
            'tier',
            'user_terms_conditions_1',
            'auth_token_1',
            'user_terms_conditions_2',
            'auth_token_2',
            'terms_1',
            'terms_2'
        }

    def test_get_pip_packages(self):
        packages = self.command.get_pip_packages()
        assert isinstance(packages, dict)

        for package in pkg_resources.working_set:
            assert packages.pop(package.project_name) == package.version

    @patch('django.core.files.File.write')
    def test_write_to_file(self, mock_write):
        path = '/dummy/path.json'
        content = '{"tetst": "contetnt"}'

        with patch("__builtin__.open", mock_open()) as mock_file:
            self.command.write_to_file(path, content)

        mock_file.assert_called_once_with(path, 'w')
        assert mock_write.called_with(content)

    @staticmethod
    def fake_process_instance(instance):
        """
        Returns all this nodes relations; the ones that it points at, and the
        ones they point at it.
        """
        graph = {
            'microsite': ['organization_1', ],
            'organization_1': ['user_1', 'user_2'],
            'tier': ['organization_1', ],
            'user_1': [],
            'user_2': [],
            'auth_token_1': ['user_1', ],
            'auth_token_2': ['user_2', ],
            'user_terms_conditions_1': ['user_1', 'terms_1', ],
            'user_terms_conditions_2': ['user_1', 'terms_2', ],
            'should_not_appear_1': ['object_not_used_1', 'object_not_used_2', ],
            'should_not_appear_2': ['object_not_used_3', ]
        }

        objects = graph.get(instance, [])
        for key, value in graph.items():
            if instance in value:
                objects.append(key)

        return instance, objects
