import factory

from factory.django import DjangoModelFactory

from bulk_email.models import Optout
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from student.tests.factories import UserFactory


class OptoutFactory(DjangoModelFactory):
    FACTORY_FOR = Optout

    user = factory.SubFactory(UserFactory)
    course_id = SlashSeparatedCourseKey('edX', 'Open_DemoX', 'edx_demo_course')
    force_disabled = False
