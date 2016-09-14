"""
Dummy factories for tests
"""
from factory import SubFactory
from factory.django import DjangoModelFactory
from student.tests.factories import UserFactory
from lms.djangoapps.ccx.models import CustomCourseForEdX


class CcxFactory(DjangoModelFactory):  # pylint: disable=missing-docstring
    class Meta(object):
        model = CustomCourseForEdX

    display_name = "Test CCX"
    id = None  # pylint: disable=invalid-name
    coach = SubFactory(UserFactory)
