"""
Factoryboy factories for Demographics.
"""

import factory

from openedx.core.djangoapps.demographics.models import UserDemographics


class UserDemographicsFactory(factory.django.DjangoModelFactory):
    """
    UserDemographics Factory
    """

    class Meta:
        model = UserDemographics
