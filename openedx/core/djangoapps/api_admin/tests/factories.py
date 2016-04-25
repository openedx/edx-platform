"""Factories for API management."""
import factory
from factory.django import DjangoModelFactory
from oauth2_provider.models import get_application_model

from microsite_configuration.tests.factories import SiteFactory
from openedx.core.djangoapps.api_admin.models import ApiAccessRequest
from student.tests.factories import UserFactory


Application = get_application_model()  # pylint: disable=invalid-name


class ApiAccessRequestFactory(DjangoModelFactory):
    """Factory for ApiAccessRequest objects."""
    class Meta(object):
        model = ApiAccessRequest

    user = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)


class ApplicationFactory(DjangoModelFactory):
    """Factory for OAuth Application objects."""
    class Meta(object):
        model = Application

    authorization_grant_type = Application.GRANT_CLIENT_CREDENTIALS
    client_type = Application.CLIENT_CONFIDENTIAL
