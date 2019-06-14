from mock import patch

import ddt
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from openedx.core.djangoapps.api_admin.management.commands import create_api_access_request
from openedx.core.djangoapps.api_admin.models import (
    ApiAccessConfig,
    ApiAccessRequest,
)
from student.tests.factories import UserFactory


@ddt.ddt
class TestCreateApiAccessRequest(TestCase):
    """ Test create_api_access_request command """

    @classmethod
    def setUpClass(cls):
        super(TestCreateApiAccessRequest, cls).setUpClass()
        cls.command = 'create_api_access_request'
        cls.user = UserFactory()

    def assert_models_exist(self, expect_request_exists, expect_config_exists):
        self.assertEqual(
            ApiAccessRequest.objects.filter(user=self.user).exists(),
            expect_request_exists
        )
        self.assertEqual(
            ApiAccessConfig.objects.filter(enabled=True).exists(),
            expect_config_exists
        )

    @ddt.data(False, True)
    def test_create_api_access_request(self, create_config):
        self.assert_models_exist(False, False)
        call_command(self.command, self.user.username, create_config=create_config)
        self.assert_models_exist(True, create_config)

    def test_config_already_exists(self):
        ApiAccessConfig.objects.create(enabled=True)
        self.assert_models_exist(False, True)
        call_command(self.command, self.user.username, create_config=True)
        self.assert_models_exist(True, True)

    def test_user_not_found(self):
        with self.assertRaisesRegex(CommandError, r'User .*? not found'):
            call_command(self.command, 'not-a-user-notfound-nope')

    @patch('openedx.core.djangoapps.api_admin.models.ApiAccessRequest.objects.create')
    def test_api_request_error(self, mocked_method):
        mocked_method.side_effect = Exception()

        self.assert_models_exist(False, False)

        with self.assertRaisesRegex(CommandError, r'Unable to create ApiAccessRequest .*'):
            call_command(self.command, self.user.username)

        self.assert_models_exist(False, False)

    @patch('openedx.core.djangoapps.api_admin.models.ApiAccessConfig.objects.get_or_create')
    def test_api_config_error(self, mocked_method):
        mocked_method.side_effect = Exception()
        self.assert_models_exist(False, False)

        with self.assertRaisesRegex(CommandError, r'Unable to create ApiAccessConfig\. .*'):
            call_command(self.command, self.user.username, create_config=True)

        self.assert_models_exist(True, False)

    def test_optional_fields(self):
        self.assert_models_exist(False, False)

        call_command(
            self.command,
            self.user.username,
            status='approved',
            reason='whatever',
            website='test-site.edx.horse'
        )
        self.assert_models_exist(True, False)
        request = ApiAccessRequest.objects.get(user=self.user)
        self.assertEqual(request.status, 'approved')
        self.assertEqual(request.reason, 'whatever')
        self.assertEqual(request.website, 'test-site.edx.horse')

    def test_site(self):
        site = Site.objects.create(domain='www.mysite.com', name='testmysite')
        call_command(self.command, self.user.username, site_name=site.name)
        request = ApiAccessRequest.objects.get(user=self.user)
        self.assertEqual(request.site, site)
        self.assertEqual(request.website, 'http://www.test-edx-example-website.edu/')

    def test_site_nonexistant(self):
        with self.assertRaisesRegex(CommandError, r'Site .*? not found'):
            call_command(self.command, self.user, site_name='nonexistant-site')
