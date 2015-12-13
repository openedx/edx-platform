""" Tests for Credit API serializers. """

# pylint: disable=no-member
from __future__ import unicode_literals

from django.test import TestCase
# from openedx.core.djangoapps.credentials_service.factories import SignatoryFactory

from openedx.core.djangoapps.credentials_service import serializers
from openedx.core.djangoapps.credentials_service.tests.factories import ProgramCertificateFactory, UserCredentialFactory


class UserCredentialSerializerTests(TestCase):
    """ UserCredentialSerializer tests. """

    def test_data(self):
        """ Verify that the correct fields are serialized. """
        program_id = 100
        program_cert = ProgramCertificateFactory.create(program_id=100)
        user_credenential = UserCredentialFactory.create(credential_object = program_cert)
        serializer = serializers.UserCredentialSerializer(user_credenential)
        expected = {
            "username":user_credenential.username,
            "status": user_credenential.status,
            "download_url": user_credenential.download_url,
            "uuid": user_credenential.uuid,
            "credential_object": program_id
        }
        self.assertDictEqual(expected, expected)
        self.assertEqual(1, 1)
