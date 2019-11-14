"""
Tests for the migrate_saml_uids management command.
"""
from __future__ import absolute_import

from django.core.management import call_command
from django.test import TestCase

from factory import LazyAttributeSequence, SubFactory
from factory.django import DjangoModelFactory
from lms.djangoapps.program_enrollments.management.commands import migrate_saml_uids
from mock import mock_open, patch
from social_django.models import UserSocialAuth
from student.tests.factories import UserFactory

_COMMAND_PATH = 'lms.djangoapps.program_enrollments.management.commands.migrate_saml_uids'

class UserSocialAuthFactory(DjangoModelFactory):
    """
    Factory for UserSocialAuth records.
    """
    class Meta(object):
        model = UserSocialAuth
    user = SubFactory(UserFactory)
    uid = LazyAttributeSequence(lambda o, n: '%s:%d' % (o.slug, n))

    class Params(object):
        slug = 'gatech'


class TestMigrateSamlUids(TestCase):
    """
    Test migrate_saml_uids command.
    """
    provider_slug = 'gatech'

    @classmethod
    def setUpClass(cls):
        super(TestMigrateSamlUids, cls).setUpClass()
        cls.command = migrate_saml_uids.Command()

    def _format_single_email_uid_pair_json(self, email, uid):
        return '[{{"email":"{email}","student_key":"{new_urn}"}}]'.format(email=email, new_urn=uid)

    def _format_slug_urn_pair(self, slug, urn):
        return '{slug}:{urn}'.format(slug=slug, urn=urn)

    def test_single_mapping(self):
        new_urn = '9001'
        auth = UserSocialAuthFactory.create(slug=self.provider_slug)
        email = auth.user.email
        old_uid = auth.uid
        with patch(
                _COMMAND_PATH + '.open',
                mock_open(read_data=self._format_single_email_uid_pair_json(email, new_urn))
        ) as pat:
            call_command(
                self.command,
                uid_mapping='./foo.json',
                saml_provider_slug=self.provider_slug
            )

        auth.refresh_from_db()
        assert auth.uid == self._format_slug_urn_pair(self.provider_slug, new_urn)
        assert not auth.uid == old_uid
