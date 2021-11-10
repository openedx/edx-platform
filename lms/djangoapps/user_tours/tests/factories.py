""" Factories for User Tours. """

import factory
from factory.django import DjangoModelFactory

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.user_tours.models import UserTour


class UserTourFactory(DjangoModelFactory):
    """
    Factory for UserTour.
    Will make user for you if not provided.
    Defaults to a brand new user's UserTour experience.
    """
    class Meta:
        model = UserTour

    user = factory.SubFactory(UserFactory)
