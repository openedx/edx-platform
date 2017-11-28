import string
from uuid import uuid4

import factory
from factory.fuzzy import FuzzyChoice, FuzzyText

from entitlements.models import CourseEntitlement
from student.tests.factories import UserFactory
from course_modes.helpers import CourseMode


class CourseEntitlementFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = CourseEntitlement

    uuid = factory.LazyFunction(uuid4)
    course_uuid = factory.LazyFunction(uuid4)
    mode = FuzzyChoice([CourseMode.VERIFIED, CourseMode.PROFESSIONAL])
    user = factory.SubFactory(UserFactory)
    order_number = FuzzyText(prefix='TEXTX', chars=string.digits)
    enrollment_course_run = None
