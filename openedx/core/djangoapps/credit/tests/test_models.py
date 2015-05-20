""" Tests for credit course models """

import ddt

from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.credit.exceptions import InvalidCreditRequirements
from openedx.core.djangoapps.credit.models import CreditCourse, CreditRequirement
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@ddt.ddt
class ModelTestCases(ModuleStoreTestCase):
    """ Tests for credit course models """

    def setUp(self, **kwargs):
        super(ModelTestCases, self).setUp()
        self.course_key = CourseKey.from_string("edX/DemoX/Demo_Course")

    @ddt.data(False, True)
    def test_is_credit_course(self, is_credit):
        CreditCourse(course_key=self.course_key, enabled=is_credit).save()
        if is_credit:
            self.assertTrue(CreditCourse.is_credit_course(self.course_key))
        else:
            self.assertFalse(CreditCourse.is_credit_course(self.course_key))

    def test_get_credit_course_non_existence(self):
        with self.assertRaises(CreditCourse.DoesNotExist):
            CreditCourse.get_credit_course(self.course_key)

    def test_get_credit_course(self):
        credit_course = CreditCourse(course_key=self.course_key, enabled=True)
        credit_course.save()
        self.assertEqual(credit_course, CreditCourse.get_credit_course(self.course_key))

    def test_add_course_requirement_invalid_course(self):
        with self.assertRaises(InvalidCreditRequirements):
            requirement = {
                "name": "grade",
                "configuration": {
                    "min_grade": 0.8
                }
            }
            CreditRequirement.add_course_requirement(None, requirement)

    def test_add_course_requirement_invalid_requirements(self):
        credit_course = CreditCourse(course_key=self.course_key)
        credit_course.save()
        with self.assertRaises(InvalidCreditRequirements):
            requirement = {
                "namespace": "grade",
                "configuration": "invalid configuration"
            }
            CreditRequirement.add_course_requirement(credit_course, requirement)

    def test_add_course_requirement(self):
        credit_course = self.add_credit_course()
        requirement = {
            "namespace": "grade",
            "name": "grade",
            "configuration": {
                "min_grade": 0.8
            }
        }
        self.assertIsNone(CreditRequirement.add_course_requirement(credit_course, requirement))
        requirements = CreditRequirement.get_course_requirements(self.course_key)
        self.assertEqual(len(requirements), 1)

    def test_get_course_requirements(self):
        credit_course = self.add_credit_course()
        requirement = {
            "namespace": "grade",
            "name": "grade",
            "configuration": {
                "min_grade": 0.8
            }
        }
        self.assertIsNone(CreditRequirement.add_course_requirement(credit_course, requirement))
        requirements = CreditRequirement.get_course_requirements(self.course_key)
        self.assertEqual(len(requirements), 1)

    def test_get_course_requirements_namespace(self):
        credit_course = self.add_credit_course()
        requirement = {
            "namespace": "grade",
            "name": "grade",
            "configuration": {
                "min_grade": 0.8
            }
        }
        self.assertIsNone(CreditRequirement.add_course_requirement(credit_course, requirement))

        requirement = {
            "namespace": "icrv",
            "name": "midterm",
            "configuration": ""
        }
        self.assertIsNone(CreditRequirement.add_course_requirement(credit_course, requirement))

        requirements = CreditRequirement.get_course_requirements(self.course_key)
        self.assertEqual(len(requirements), 2)
        requirements = CreditRequirement.get_course_requirements(self.course_key, namespace="grade")
        self.assertEqual(len(requirements), 1)

    def add_credit_course(self):
        """ Add the course as a credit

        Returns:
            CreditCourse object
        """
        credit_course = CreditCourse(course_key=self.course_key, enabled=True)
        credit_course.save()
        return credit_course
