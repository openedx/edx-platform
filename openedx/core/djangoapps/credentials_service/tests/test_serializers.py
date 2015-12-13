""" Tests for Credit API serializers. """

# pylint: disable=no-member
from __future__ import unicode_literals

from django.test import TestCase

from openedx.core.djangoapps.credentials_service import serializers
from openedx.core.djangoapps.credentials_service.tests.factories import (
    ProgramCertificateFactory, UserCredentialFactory, UserCredentialAttributeFactory
)


class CredentialSerializerTests(TestCase):
    """ UserCredentialSerializer tests. """

    def setUp(self):
        super(CredentialSerializerTests, self).setUp()
        self.program_id = 100
        self.program_cert = ProgramCertificateFactory.create(program_id=100)
        self.user_credenential = UserCredentialFactory.create(credential_object=self.program_cert)
        self.attr = UserCredentialAttributeFactory.create(user_credential=self.user_credenential)
        self.maxDiff = None


    def test_usercredentialserializer(self):
        serialize_data = serializers.UserCredentialSerializer(self.user_credenential)
        expected = {
            "object_id": self.user_credenential.object_id,
            "username": self.user_credenential.username,
            "status": self.user_credenential.status,
            "download_url": self.user_credenential.download_url,
            "uuid": self.user_credenential.uuid,
            "credential_object": self.program_id,
            "attributes": [
                {
                    "user_credential": self.attr.id,
                    "namespace": self.attr.namespace,
                    "name": self.attr.name,
                    "value": self.attr.value
                }
            ]
        }
        self.assertDictEqual(serialize_data.data, expected)

    def test_usercredentialattributeSerializer(self):
        serialize_data = serializers.UserCredentialAttributeSerializer(self.attr)
        expected = {
            "user_credential": self.attr.id,
            "namespace": self.attr.namespace,
            "name": self.attr.name,
            "value": self.attr.value
        }

        self.assertDictEqual(serialize_data.data, expected)

    def test_programcertificatebaseserializer(self):
        serialize_data = serializers.ProgramCertificateBaseSerializer(self.program_cert)
        expected = {
            "program_id": self.program_cert.program_id
        }

        self.assertDictEqual(serialize_data.data, expected)

    def test_programcertificateserializer(self):

        # user_cred_2 = UserCredentialFactory.create(credential_object=self.program_cert)
        serialize_data = serializers.ProgramCertificateSerializer(self.program_cert)
        expected = {
            'program_id': '100',
            'user_credential': [{
                "object_id": self.user_credenential.object_id,
                "username": self.user_credenential.username,
                "status": self.user_credenential.status,
                "download_url": self.user_credenential.download_url,
                "uuid": self.user_credenential.uuid,
                "credential_object": self.program_id,
                "attributes": [
                    {
                        "user_credential": self.attr.id,
                        "namespace": self.attr.namespace,
                        "name": self.attr.name,
                        "value": self.attr.value
                    }
                ]
            }]
        }

        self.assertDictEqual(serialize_data.data, expected)

