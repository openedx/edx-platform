"""
Dummy factories for tests
"""
from factory import SubFactory, Sequence
from factory.django import DjangoModelFactory
from student.tests.factories import UserFactory
from lms.djangoapps.ccx.models import CustomCourseForEdX


class CcxFactory(DjangoModelFactory):  # pylint: disable=missing-docstring
    class Meta(object):
        model = CustomCourseForEdX

    display_name = Sequence(lambda n: 'Test CCX #{0}'.format(n))  # pylint: disable=unnecessary-lambda
    id = None  # pylint: disable=invalid-name
    coach = SubFactory(UserFactory)
