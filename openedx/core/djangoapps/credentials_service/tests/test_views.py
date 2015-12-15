"""
Tests for credentials service views.
"""
from __future__ import unicode_literals
import json

from django.core.urlresolvers import reverse
from django.test import TestCase
from openedx.core.djangoapps.credentials_service.models import UserCredential

from openedx.core.djangoapps.credentials_service import serializers
from openedx.core.djangoapps.credentials_service.tests.factories import ProgramCertificateFactory, \
    UserCredentialFactory, UserFactory, UserCredentialAttributeFactory
from openedx.core.djangoapps.credentials_service.tests.mixin import UserCredentialSerializer


JSON_CONTENT_TYPE = 'application/json'


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

    def _attempt_update_user_credential(self, data):
        """ Helper method that attempts to patch an existing credential object.

        Arguments:
          data (dict): Data to be converted to JSON and sent to the API.

        Returns:
          Response: HTTP response from the API.
        """

        path = reverse("credentials:v1:users_credentials-detail", args=[self.user_credential.username])
        return self.client.patch(path=path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)

    def test_patch_user_credentials(self):
        """ Verify that status of credentials will be updated with patch request. """
        data = {
            "id": 1,
            "status": "revoked",
            }
        response = self._attempt_update_user_credential(data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['status'], data['status'])

    def test_patch_only_status(self):
        """ Verify that users allow to update only status of credentials will
         be updated with patch request.
         """
        data = {
            "id": 1,
            "download_url": "dummy-url",
            }
        response = self._attempt_update_user_credential(data)

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(json.loads(response.content), {'message': 'Only status of credential is allowed to update'})

    def _attempt_create_user_credentials(self, data):
        """ Helper method that attempts to create user credentials.

        Arguments:
          data (dict): Data to be converted to JSON and sent to the API.

        Returns:
          Response: HTTP response from the API.
        """
        path = reverse("credentials:v1:users_credentials-list")
        return self.client.post(path=path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)

    def test_create_user_credential(self):
        """ Verify the endpoint supports the creation of new user credentials. """

        data = {
            "credentials": [
                {
                    "username": "user1",
                    "program_id": 1100,
                    "attributes": [
                        {
                            "namespace": "white-list",
                            "name": "grade",
                            "value": "8.0"
                        }
                    ]
                },
                {
                    "username": "user2",
                    "program_id": 1100,
                    "attributes": [
                        {
                            "namespace": "white-list",
                            "name": "grade",
                            "value": "10"
                        },
                        {
                            "namespace": "white-list",
                            "name": "grade",
                            "value": "10"
                        }
                    ]
                }
            ]
        }

        response = self._attempt_create_user_credentials(data)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(UserCredential.objects.filter(username='user1').exists())

    def test_create_with_invalid_program_id(self):
        """ Verify the endpoint doesn't supports the creation of new user credentials,
        if any program_id doesn't exist. Transaction will be roll backed and no credential
        will be inserted in database.
        """
        data = {
            "credentials": [
                {
                    "username": "user1",
                    "program_id": 1100,
                    "attributes": [
                        {
                            "namespace": "white-list",
                            "name": "grade",
                            "value": "8.0"
                        }
                    ]
                },
                {
                    "username": "user2",
                    "program_id": 0000,
                    "attributes": [
                        {
                            "namespace": "white-list",
                            "name": "grade",
                            "value": "10"
                        },
                    ]
                }
            ]
        }

        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.status_code, 404)

        # Verify that credentials for 'user1' are also not exists.
        self.assertFalse(UserCredential.objects.filter(username='user1').exists())
