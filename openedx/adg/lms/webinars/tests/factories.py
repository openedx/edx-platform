"""
All model factories for webinars
"""
from datetime import timedelta

import factory
from django.utils.timezone import now

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.lms.webinars.models import Webinar


class WebinarFactory(factory.DjangoModelFactory):
    """
    Factory for Webinar model
    """

    class Meta:
        model = Webinar

    title = factory.Faker('sentence')
    description = factory.Faker('sentence')
    presenter = factory.SubFactory(UserFactory)
    banner = factory.django.ImageField()
    language = factory.Faker('word')

    start_time = now() + timedelta(hours=1)
    end_time = now() + timedelta(hours=2)
    created_by = factory.SubFactory(UserFactory)
