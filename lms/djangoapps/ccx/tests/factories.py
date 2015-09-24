"""
Dummy factories for tests
"""
from factory import SubFactory
from factory.django import DjangoModelFactory
from student.tests.factories import UserFactory
from ccx.models import CustomCourseForEdX  # pylint: disable=import-error


class CcxFactory(DjangoModelFactory):  # pylint: disable=missing-docstring
    class Meta(object):  # pylint: disable=missing-docstring
        model = CustomCourseForEdX
    display_name = "Test CCX"
    id = None  # pylint: disable=redefined-builtin, invalid-name
    coach = SubFactory(UserFactory)
