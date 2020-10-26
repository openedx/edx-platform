"""
Tests the ``create_dot_application`` management command.
"""
from __future__ import absolute_import, unicode_literals

import ddt

from django.core.management import call_command
from django.test import TestCase
from oauth2_provider.models import get_application_model

from student.tests.factories import UserFactory

from ..create_dot_application import Command


Application = get_application_model()


@ddt.ddt
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

    @ddt.data(
        (None, None, None, None),
        (None, None, 'client-abc', None),
        (None, None, None, 'great-big-secret'),
        ('password', True, 'client-dce', 'has-a-great-big-secret'),
    )
    @ddt.unpack
    def test_create_dot_application(self, grant_type, public, client_id, client_secret):
        # Add optional arguments if provided
        call_args = ['testing_application', self.user.username]
        if grant_type:
            call_args.append('--grant-type')
            call_args.append(grant_type)
        else:
            grant_type = Application.GRANT_CLIENT_CREDENTIALS

        if public:
            call_args.append('--public')
            client_type = Application.CLIENT_PUBLIC
        else:
            client_type = Application.CLIENT_CONFIDENTIAL

        if client_id:
            call_args.append('--client-id')
            call_args.append(client_id)
        if client_secret:
            call_args.append('--client-secret')
            call_args.append(client_secret)

        call_command(Command(), *call_args)

        apps = Application.objects.filter(name='testing_application')
        self.assertEqual(1, len(apps))
        application = apps[0]
        self.assertEqual('testing_application', application.name)
        self.assertEqual(self.user, application.user)
        self.assertEqual(grant_type, application.authorization_grant_type)
        self.assertEqual(client_type, application.client_type)
        self.assertEqual('', application.redirect_uris)

        if client_id:
            self.assertEqual(client_id, application.client_id)
        if client_secret:
            self.assertEqual(client_secret, application.client_secret)

        # When called a second time with the same arguments, the command should
        # exit gracefully without creating a second application.
        call_command(Command(), *call_args)
        apps = Application.objects.filter(name='testing_application')
        self.assertEqual(1, len(apps))
