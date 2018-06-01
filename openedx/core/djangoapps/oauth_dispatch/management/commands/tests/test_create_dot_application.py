"""
Tests the ``create_dot_application`` management command.
"""
from __future__ import absolute_import, unicode_literals

from django.core.management import call_command
from django.test import TestCase
from oauth2_provider.models import get_application_model

from student.tests.factories import UserFactory

from ..create_dot_application import Command


Application = get_application_model()


class TestCreateDotApplication(TestCase):
    """
    Tests the ``create_dot_application`` management command.
    """
    def setUp(self):
        super(TestCreateDotApplication, self).setUp()
        self.user = UserFactory.create()

    def tearDown(self):
        super(TestCreateDotApplication, self).tearDown()
        Application.objects.filter(user=self.user).delete()

    def test_create_dot_application(self):
        call_command(Command(), 'testing_application', self.user.username)

        apps = Application.objects.filter(name='testing_application')
        self.assertEqual(1, len(apps))
        application = apps[0]
        self.assertEqual('testing_application', application.name)
        self.assertEqual(self.user, application.user)
        self.assertEqual(Application.GRANT_CLIENT_CREDENTIALS, application.authorization_grant_type)
        self.assertEqual(Application.CLIENT_CONFIDENTIAL, application.client_type)
        self.assertEqual('', application.redirect_uris)

        # When called a second time with the same arguments, the command should
        # exit gracefully without creating a second application.
        call_command(Command(), 'testing_application', self.user.username)
        apps = Application.objects.filter(name='testing_application')
        self.assertEqual(1, len(apps))
