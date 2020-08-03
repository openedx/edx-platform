import factory
from factory.django import DjangoModelFactory
from faker.providers import internet

from custom_settings.models import CustomSettings
from openedx.features.philu_utils.model_factory import random_course_key

factory.Faker.add_provider(internet)


class CustomSettingsFactory(DjangoModelFactory):
    class Meta(object):
        model = CustomSettings
        django_get_or_create = ('course_short_id',)

    id = factory.LazyFunction(random_course_key)
    tags = factory.Faker('word')
    course_short_id = factory.Faker('random_int')
    seo_tags = '{"title":"test", "description":"test"}'
    course_open_date = factory.Faker('date_time')
