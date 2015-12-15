"""
Tests for credentials service views.
"""
from __future__ import unicode_literals
import json

from django.core.urlresolvers import reverse
from django.test import TestCase

from student.tests.factories import UserFactory
from openedx.core.djangoapps.credentials_service import serializers
from openedx.core.djangoapps.credentials_service.tests.factories import ProgramCertificateFactory, \
    UserCredentialFactory, \
    UserCredentialAttributeFactory
from openedx.core.djangoapps.credentials_service.tests.mixin import UserCredentialSerializer


class TestGenerateProgramsCredentialView(TestCase, UserCredentialSerializer):
    def setUp(self):
        super(TestGenerateProgramsCredentialView, self).setUp()

        user = UserFactory()
        self.client.login(username=user.username, password=user.password)

        # create credentials for user
        self.program_id = 1100
        self.program_cert = ProgramCertificateFactory.create(program_id=self.program_id)
        self.user_credential = UserCredentialFactory.create(credential=self.program_cert)
        self.attr = UserCredentialAttributeFactory.create(user_credential=self.user_credential)
        self.maxDiff = None

    def test_get_user_credential(self):
        """ Verify a single user credential is returned. """

        path = reverse("credentials:v1:users_credentials-detail", args=[self.user_credential.username])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)

        serializer = serializers.UserCredentialSerializer(self.user_credential)
        self.assertDictEqual(json.loads(response.content), serializer.data)

    def test_list_users_credentials(self):
        """ Verify a list end point of user credentials return list of
        credentials.
        """
        dummy_program_cert = ProgramCertificateFactory.create(program_id=1101)
        dummy_user_credential = UserCredentialFactory.create(credential=dummy_program_cert)

        response = self.client.get(path=reverse("credentials:v1:users_credentials-list"))
        self.assertEqual(response.status_code, 200)
        results = [
            serializers.UserCredentialSerializer(self.user_credential).data,
            serializers.UserCredentialSerializer(dummy_user_credential).data
        ]

        expected = {'count': 2, 'next': None, 'previous': None, 'num_pages': 1, 'results': results}

        self.assertDictEqual(json.loads(response.content), expected)

    def test_get_programs_credential(self):
        """ Verify a single program credential is returned. """

        path = reverse("credentials:v1:programs-detail", args=[self.program_id])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)

        serializer = serializers.ProgramCertificateSerializer(self.program_cert)
        self.assertDictEqual(json.loads(response.content), serializer.data)

    def test_list_programs_credential(self):
        """ Verify a list end point of programs credentials return list of
        credentials.
        """
        dummy_program_cert = ProgramCertificateFactory.create(program_id=1102)
        response = self.client.get(path=reverse("credentials:v1:programs-list"))
        self.assertEqual(response.status_code, 200)
        results = [
            serializers.ProgramCertificateSerializer(self.program_cert).data,
            serializers.ProgramCertificateSerializer(dummy_program_cert).data
        ]

        expected = {'count': 2, 'next': None, 'previous': None, 'num_pages': 1, 'results': results}
        self.assertDictEqual(json.loads(response.content), expected)
