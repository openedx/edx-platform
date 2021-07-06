"""
All model factories for webinars
"""
from datetime import timedelta

import factory
from django.utils.timezone import now

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.lms.webinars.models import Webinar, WebinarRegistration


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
    language = factory.Iterator(['ar', 'en'])
    meeting_link = factory.Faker('url')
    start_time = now() + timedelta(hours=1)
    end_time = now() + timedelta(hours=2)
    created_by = factory.SubFactory(UserFactory)
    is_published = True


class WebinarRegistrationFactory(factory.DjangoModelFactory):
    """
    Factory for WebinarRegistration model
    """

    webinar = factory.SubFactory(WebinarFactory)
    user = factory.SubFactory(UserFactory)
    is_registered = True

    class Meta:
        model = WebinarRegistration
        django_get_or_create = ('user', 'webinar')
