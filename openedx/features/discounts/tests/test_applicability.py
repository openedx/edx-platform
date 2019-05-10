"""Tests of openedx.features.discounts.applicability"""
# -*- coding: utf-8 -*-

from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..applicability import can_recieve_discount


class TestApplicability(ModuleStoreTestCase):
    """
    Applicability determines if this combination of user and course can receive a discount. Make
    sure that all of the business conditions work.
    """

    def setUp(self):
        super(TestApplicability, self).setUp()
        self.user = UserFactory.create()
        self.course = CourseFactory.create(run='test', display_name='test')

    def test_can_recieve_discount(self):
        # Right now, no one should be able to recieve the discount
        applicability = can_recieve_discount(user=self.user, course_key_string=self.course.id)
        self.assertEqual(applicability, False)
