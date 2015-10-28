"""
Tests for the Credit xBlock service
"""

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from openedx.core.djangoapps.credit.services import CreditService
from openedx.core.djangoapps.credit.models import CreditCourse
from openedx.core.djangoapps.credit.api.eligibility import set_credit_requirements

from student.models import CourseEnrollment, UserProfile


class CreditServiceTests(ModuleStoreTestCase):
    """
    Tests for the Credit xBlock service
    """

    def setUp(self, **kwargs):
        super(CreditServiceTests, self).setUp()

        self.service = CreditService()
        self.course = CourseFactory.create(org='edX', number='DemoX', display_name='Demo_Course')
        self.credit_course = CreditCourse.objects.create(course_key=self.course.id, enabled=True)
        self.profile = UserProfile.objects.create(user_id=self.user.id, name='Foo Bar')

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

    def test_inactive_enrollment(self):
        """
        Makes sure that get_credit_state returns None if the user's enrollment is
        inactive
        """

        enrollment = CourseEnrollment.enroll(self.user, self.course.id)
        enrollment.is_active = False
        enrollment.save()

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

    def test_no_profile_name(self):
        """
        Makes sure that get_credit_state returns None if the user does not
        have a corresponding UserProfile. This shouldn't happen in
        real environments
        """

        profile = UserProfile.objects.get(user_id=self.user.id)
        profile.delete()

        self.assertIsNone(self.service.get_credit_state(self.user.id, self.course.id))

    def test_get_and_set_credit_state(self):
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
        self.service.set_credit_requirement_status(
            self.user.id,
            self.course.id,
            'grade',
            'grade'
        )

        credit_state = self.service.get_credit_state(self.user.id, self.course.id)

        self.assertIsNotNone(credit_state)
        self.assertEqual(credit_state['enrollment_mode'], 'honor')
        self.assertEqual(credit_state['profile_fullname'], 'Foo Bar')
        self.assertEqual(len(credit_state['credit_requirement_status']), 1)
        self.assertEqual(credit_state['credit_requirement_status'][0]['name'], 'grade')
        self.assertEqual(credit_state['credit_requirement_status'][0]['status'], 'satisfied')

    def test_bad_user(self):
        """
        Try setting requirements status with a bad user_id
        """

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
        retval = self.service.set_credit_requirement_status(
            0,
            self.course.id,
            'grade',
            'grade'
        )
        self.assertIsNone(retval)

    def test_course_id_string(self):
        """
        Make sure we can pass a course_id (string) and get back correct results as well
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
        self.service.set_credit_requirement_status(
            self.user.id,
            unicode(self.course.id),
            'grade',
            'grade'
        )

        credit_state = self.service.get_credit_state(self.user.id, unicode(self.course.id))

        self.assertIsNotNone(credit_state)
        self.assertEqual(credit_state['enrollment_mode'], 'honor')
        self.assertEqual(credit_state['profile_fullname'], 'Foo Bar')
        self.assertEqual(len(credit_state['credit_requirement_status']), 1)
        self.assertEqual(credit_state['credit_requirement_status'][0]['name'], 'grade')
        self.assertEqual(credit_state['credit_requirement_status'][0]['status'], 'satisfied')
