"""
Sharable utilities for testing program enrollments
"""

from factory import LazyAttributeSequence, SubFactory
from factory.django import DjangoModelFactory
from social_django.models import UserSocialAuth

from common.djangoapps.student.tests.factories import UserFactory


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
