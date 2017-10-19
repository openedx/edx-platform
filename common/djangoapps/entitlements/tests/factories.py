import string
import uuid

import factory
from factory.fuzzy import FuzzyChoice, FuzzyText

from entitlements.models import CourseEntitlement
from student.tests.factories import UserFactory


class CourseEntitlementFactory(factory.django.DjangoModelFactory):
    class Meta(object):
        model = CourseEntitlement

    course_uuid = uuid.uuid4()
    mode = FuzzyChoice(['verified', 'profesional'])
    user = factory.SubFactory(UserFactory)
    order_number = FuzzyText(prefix='TEXTX', chars=string.digits)
