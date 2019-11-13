"""
Tests for the migrate_saml_uids management command.
"""
from __future__ import absolute_import

from django.core.management import call_command
from django.test import TestCase

from factory import LazyAttributeSequence, SubFactory
from factory.django import DjangoModelFactory
from lms.djangoapps.program_enrollments.management.commands import migrate_saml_uids
from social_django.models import UserSocialAuth
from student.tests.factories import UserFactory


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

    def _format_email_uid_pair(self, email, uid):
        return '{email}:{uid}'.format(email=email, uid=uid)

    def _format_slug_urn_pair(self, slug, urn):
        return '{slug}:{urn}'.format(slug=slug, urn=urn)

    def test_single_mapping(self):
        new_urn = '9001'
        auth = UserSocialAuthFactory.create(slug=self.provider_slug)
        email = auth.user.email
        old_uid = auth.uid
        call_command(
            self.command,
            uid_mapping=self._format_email_uid_pair(email, new_urn),
            saml_provider_slug=self.provider_slug
        )

        auth.refresh_from_db()
        assert auth.uid == self._format_slug_urn_pair(self.provider_slug, new_urn)
        assert not auth.uid == old_uid
