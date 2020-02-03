import factory

from faker.providers import internet

from nodebb.constants import CONVERSATIONALIST_ENTRY_INDEX
from openedx.features.badging.models import Badge, UserBadge
from openedx.features.badging.constants import CONVERSATIONALIST
from opaque_keys.edx.keys import CourseKey
from student.tests.factories import UserFactory

factory.Faker.add_provider(internet)


class BadgeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Badge

    name = factory.Faker('name')
    image = factory.Faker('uri_path', deep=None)
    threshold = 10
    type = CONVERSATIONALIST[CONVERSATIONALIST_ENTRY_INDEX]


class UserBadgeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserBadge

    badge = factory.SubFactory(BadgeFactory)
    user = factory.SubFactory(UserFactory)
    course_id = CourseKey.from_string('abc/123/course')
    community_id = 1
