"""Factories for API management."""
import factory
from factory.django import DjangoModelFactory

from microsite_configuration.tests.factories import SiteFactory
from openedx.core.djangoapps.api_admin.models import ApiAccessRequest
from student.tests.factories import UserFactory


class ApiAccessRequestFactory(DjangoModelFactory):
    """Factory for ApiAccessRequest objects."""
    class Meta(object):
        model = ApiAccessRequest

    user = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)
