"""
Dummy factories for tests
"""


from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.ccx.models import CustomCourseForEdX


# pylint: disable=missing-class-docstring
class CcxFactory(DjangoModelFactory):
    class Meta:
        model = CustomCourseForEdX

    display_name = Sequence(lambda n: f'Test CCX #{n}')  # pylint: disable=unnecessary-lambda
    id = None  # pylint: disable=invalid-name
    coach = SubFactory(UserFactory)
