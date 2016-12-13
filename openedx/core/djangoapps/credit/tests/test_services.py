"""
Tests for the Credit xBlock service
"""

import ddt
from nose.plugins.attrib import attr
from course_modes.models import CourseMode
from unittest import skip

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from openedx.core.djangoapps.credit.services import CreditService
from openedx.core.djangoapps.credit.models import CreditCourse
from openedx.core.djangoapps.credit.api.eligibility import set_credit_requirements

from student.models import CourseEnrollment, UserProfile


@skip("Jenkins DEBUG, nomerge")
@attr(shard=2)
@ddt.ddt
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

    def enroll(self, course_id=None, mode=CourseMode.VERIFIED):
        """
        Enroll the test user in the given course's mode. Use course/mode if they are
        provided.
        """
        if course_id is None:
            course_id = self.course.id
        return CourseEnrollment.enroll(self.user, course_id, mode=mode)

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

        enrollment = self.enroll()
        enrollment.is_active = False
        enrollment.save()

        self.assertIsNone(self.service.get_credit_state(self.user.id, self.course.id))

    def test_not_credit_course(self):
        """
        Makes sure that get_credit_state returns None if the test course is not
        Credit eligible
        """

        self.enroll()

        self.credit_course.enabled = False
        self.credit_course.save()

        credit_state = self.service.get_credit_state(self.user.id, self.course.id)
        self.assertIsNotNone(credit_state)
        self.assertFalse(credit_state['is_credit_course'])

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

        self.assertTrue(self.service.is_credit_course(self.course.id))

        self.enroll()

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
        self.assertTrue(credit_state['is_credit_course'])
        self.assertEqual(credit_state['enrollment_mode'], 'verified')
        self.assertEqual(credit_state['profile_fullname'], 'Foo Bar')
        self.assertEqual(len(credit_state['credit_requirement_status']), 1)
        self.assertEqual(credit_state['credit_requirement_status'][0]['name'], 'grade')
        self.assertEqual(credit_state['credit_requirement_status'][0]['status'], 'satisfied')

    def test_remove_credit_requirement_status(self):
        """
        Happy path when deleting the requirement status.
        """
        self.assertTrue(self.service.is_credit_course(self.course.id))

        self.enroll()

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

        # now the status should be "satisfied" when looking at the credit_requirement_status list
        credit_state = self.service.get_credit_state(self.user.id, self.course.id)
        self.assertEqual(credit_state['credit_requirement_status'][0]['status'], "satisfied")

        # remove the requirement status.
        self.service.remove_credit_requirement_status(
            self.user.id,
            self.course.id,
            'grade',
            'grade'
        )

        # now the status should be None when looking at the credit_requirement_status list
        credit_state = self.service.get_credit_state(self.user.id, self.course.id)
        self.assertEqual(credit_state['credit_requirement_status'][0]['status'], None)

    def test_invalid_user(self):
        """
        Try removing requirement status with a invalid user_id
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
            self.user.id,
            self.course.id,
            'grade',
            'grade'
        )
        self.assertIsNone(retval)

        # remove the requirement status with the invalid user id
        retval = self.service.remove_credit_requirement_status(
            0,
            self.course.id,
            'grade',
            'grade'
        )
        self.assertIsNone(retval)

    def test_remove_status_non_credit(self):
        """
        assert that we can still try to update a credit status but return quickly if
        a course is not credit eligible
        """

        no_credit_course = CourseFactory.create(org='NoCredit', number='NoCredit', display_name='Demo_Course')

        self.assertFalse(self.service.is_credit_course(no_credit_course.id))

        self.enroll(no_credit_course.id)

        # this should be a no-op
        self.service.remove_credit_requirement_status(
            self.user.id,
            no_credit_course.id,
            'grade',
            'grade'
        )

        credit_state = self.service.get_credit_state(self.user.id, no_credit_course.id)

        self.assertIsNotNone(credit_state)
        self.assertFalse(credit_state['is_credit_course'])
        self.assertEqual(len(credit_state['credit_requirement_status']), 0)

    def test_course_name(self):
        """
        Make sure we can get back the optional course name
        """

        self.enroll()

        # make sure it is not returned by default
        credit_state = self.service.get_credit_state(self.user.id, self.course.id)
        self.assertNotIn('course_name', credit_state)

        # now make sure it is in there when we pass in the flag
        credit_state = self.service.get_credit_state(self.user.id, self.course.id, return_course_info=True)
        self.assertIn('course_name', credit_state)
        self.assertEqual(credit_state['course_name'], self.course.display_name)

    def test_set_status_non_credit(self):
        """
        assert that we can still try to update a credit status but return quickly if
        a course is not credit eligible
        """

        no_credit_course = CourseFactory.create(org='NoCredit', number='NoCredit', display_name='Demo_Course')

        self.assertFalse(self.service.is_credit_course(no_credit_course.id))

        self.enroll(no_credit_course.id)

        # this should be a no-op
        self.service.set_credit_requirement_status(
            self.user.id,
            no_credit_course.id,
            'grade',
            'grade'
        )

        credit_state = self.service.get_credit_state(self.user.id, no_credit_course.id)

        self.assertIsNotNone(credit_state)
        self.assertFalse(credit_state['is_credit_course'])
        self.assertEqual(len(credit_state['credit_requirement_status']), 0)

    @ddt.data(
        CourseMode.AUDIT,
        CourseMode.HONOR,
        CourseMode.CREDIT_MODE
    )
    def test_set_status_non_verified_enrollment(self, mode):
        """
        Test that we can still try to update a credit status but return quickly if
        user has non-credit eligible enrollment.
        """
        self.enroll(mode=mode)

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

        # this should be a no-op
        self.service.set_credit_requirement_status(
            self.user.id,
            self.course.id,
            'grade',
            'grade'
        )
        # Verify credit requirement status for user in the course should be None.
        credit_state = self.service.get_credit_state(self.user.id, self.course.id)
        self.assertIsNotNone(credit_state)
        self.assertEqual(credit_state['enrollment_mode'], mode)
        self.assertEqual(len(credit_state['credit_requirement_status']), 1)
        self.assertIsNone(credit_state['credit_requirement_status'][0]['status'])
        self.assertIsNone(credit_state['credit_requirement_status'][0]['status_date'])

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

        self.enroll()

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
        self.assertEqual(credit_state['enrollment_mode'], 'verified')
        self.assertEqual(credit_state['profile_fullname'], 'Foo Bar')
        self.assertEqual(len(credit_state['credit_requirement_status']), 1)
        self.assertEqual(credit_state['credit_requirement_status'][0]['name'], 'grade')
        self.assertEqual(credit_state['credit_requirement_status'][0]['status'], 'satisfied')
