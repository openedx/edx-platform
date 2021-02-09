"""
Factories for registration-extension app
"""
import factory

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.lms.applications.tests.factories import BusinessLineFactory
from openedx.adg.lms.registration_extension.models import ExtendedUserProfile


class ExtendedUserProfileFactory(factory.DjangoModelFactory):
    """
    Factory for ExtendedUserProfile model
    """

    class Meta:
        model = ExtendedUserProfile

    user = factory.SubFactory(UserFactory)
    company = factory.SubFactory(BusinessLineFactory)
    saudi_national = False
