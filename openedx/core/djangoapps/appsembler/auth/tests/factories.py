"""
We import factories from other modules here so we have a single place our tests
to import for factories. This helps reduce platform coupling
"""
import factory
from factory.django import DjangoModelFactory

from openedx.core.djangoapps.oauth_dispatch.tests.factories import (
    ApplicationFactory
)
from openedx.core.djangoapps.appsembler.auth.models import TrustedApplication


class TrustedApplicationFactory(DjangoModelFactory):
    class Meta:
        model = TrustedApplication

    application = factory.SubFactory(ApplicationFactory)
