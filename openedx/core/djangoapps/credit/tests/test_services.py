"""
Tests for the Credit xBlock service
"""

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from openedx.core.djangoapps.credit.services import CreditService
from openedx.core.djangoapps.credit.models import CreditCourse, CreditRequirementStatus, CreditRequirement
from openedx.core.djangoapps.credit.api.eligibility import (
    set_credit_requirements,
    set_credit_requirement_status
)

from student.models import CourseEnrollment


class CreditServiceTests(ModuleStoreTestCase):
    """
    Tests for the Credit xBlock service
    """

    def setUp(self, **kwargs):
        super(CreditServiceTests, self).setUp()

        self.service = CreditService()
        self.course = CourseFactory.create(org='edX', number='DemoX', display_name='Demo_Course')
        self.credit_course = CreditCourse.objects.create(course_key=self.course.id, enabled=True)

    def test_user_not_found(self):
        """
        Makes sure that get_credit_state returns None if user_id cannot be found
        """

        self.assertIsNone(self.service.get_credit_state(0, self.course.id))

    def test_user_not_enrolled(self):
        """
        Makes sure that get_credit_state returns None if user_id is not enrolled
        in the test course
        """

        self.assertIsNone(self.service.get_credit_state(self.user.id, self.course.id))

    def test_not_credit_course(self):
        """
        Makes sure that get_credit_state returns None if the test course is not
        Credit eligible
        """

        CourseEnrollment.enroll(self.user, self.course.id)

        self.credit_course.enabled = False
        self.credit_course.save()

        self.assertIsNone(self.service.get_credit_state(self.user.id, self.course.id))

    def test_get_credit_state(self):
        """
        Happy path through the service
        """

        CourseEnrollment.enroll(self.user, self.course.id)

        # set course requirements
        set_credit_requirements(
            self.course.id,
            [
                {
                    "namespace": "grade",
                    "name": "grade",
                    "display_name": "Grade",
                    "criteria": {
                        "min_grade": 0.8
                    },
                },
            ]
        )

        # mark the grade as satisfied
        set_credit_requirement_status(self.user.username, self.course.id, 'grade', 'grade')

        credit_state = self.service.get_credit_state(self.user.id, self.course.id)

        self.assertIsNotNone(credit_state)
        self.assertEqual(credit_state['enrollment_mode'], 'honor')
        self.assertEqual(len(credit_state['credit_requirements']), 1)
        self.assertEqual(credit_state['credit_requirements'][0]['name'], 'grade')

        self.assertEqual(len(credit_state['credit_requirement_status']), 1)
        self.assertEqual(credit_state['credit_requirement_status'][0]['status'], 'satisfied')
