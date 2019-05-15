"""
Dummy factories for tests
"""
from __future__ import absolute_import

from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory

from lms.djangoapps.ccx.models import CustomCourseForEdX
from student.tests.factories import UserFactory


class CcxFactory(DjangoModelFactory):  # pylint: disable=missing-docstring
    class Meta(object):
        model = CustomCourseForEdX

    display_name = Sequence(lambda n: u'Test CCX #{0}'.format(n))  # pylint: disable=unnecessary-lambda
    id = None  # pylint: disable=invalid-name
    coach = SubFactory(UserFactory)
