"""
Dummy factories for tests
"""


from factory import Sequence, SubFactory  # lint-amnesty, pylint: disable=import-error
from factory.django import DjangoModelFactory  # lint-amnesty, pylint: disable=import-error

from lms.djangoapps.ccx.models import CustomCourseForEdX
from common.djangoapps.student.tests.factories import UserFactory


# pylint: disable=missing-class-docstring
class CcxFactory(DjangoModelFactory):
    class Meta(object):
        model = CustomCourseForEdX

    display_name = Sequence(lambda n: u'Test CCX #{0}'.format(n))  # pylint: disable=unnecessary-lambda
    id = None  # pylint: disable=invalid-name
    coach = SubFactory(UserFactory)
