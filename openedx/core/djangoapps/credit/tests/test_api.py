""" Tests for credit course api """
import ddt

from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.credit.api import (
    get_credit_requirements, set_credit_requirements, _get_requirements_to_disable
)
from openedx.core.djangoapps.credit.exceptions import InvalidCreditRequirements, InvalidCreditCourse
from openedx.core.djangoapps.credit.models import CreditCourse, CreditRequirement
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@ddt.ddt
class ApiTestCases(ModuleStoreTestCase):
    """ Tests for credit course api """

    def setUp(self, **kwargs):
        super(ApiTestCases, self).setUp()
        self.course_key = CourseKey.from_string("edX/DemoX/Demo_Course")

    @ddt.data(
        [
            {
                "namespace": "grade",
                "criteria": {
                    "min_grade": 0.8
                }
            }
        ],
        [
            {
                "name": "grade",
                "criteria": {
                    "min_grade": 0.8
                }
            }
        ],
        [
            {
                "namespace": "grade",
                "name": "grade",
            }
        ]
    )
    def test_set_credit_requirements_invalid_requirements(self, requirements):
        self.add_credit_course()
        with self.assertRaises(InvalidCreditRequirements):
            set_credit_requirements(self.course_key, requirements)

    def test_set_credit_requirements_invalid_course(self):
        requirements = [
            {
                "namespace": "grade",
                "name": "grade",
                "criteria": {}
            }
        ]
        with self.assertRaises(InvalidCreditCourse):
            set_credit_requirements(self.course_key, requirements)
        self.add_credit_course(enabled=False)
        with self.assertRaises(InvalidCreditCourse):
            set_credit_requirements(self.course_key, requirements)

    def test_set_get_credit_requirements(self):
        self.add_credit_course()
        requirements = [
            {
                "namespace": "grade",
                "name": "grade",
                "criteria": {
                    "min_grade": 0.8
                }
            },
            {
                "namespace": "grade",
                "name": "grade",
                "criteria": {
                    "min_grade": 0.8
                }
            }
        ]
        set_credit_requirements(self.course_key, requirements)
        self.assertEqual(len(get_credit_requirements(self.course_key)), 1)

    def test_disable_credit_requirements(self):
        self.add_credit_course()
        requirements = [
            {
                "namespace": "grade",
                "name": "grade",
                "criteria": {
                    "min_grade": 0.8
                }
            },
            {
                "namespace": "grade",
                "name": "grade",
                "criteria": {
                    "min_grade": 0.8
                }
            }
        ]
        set_credit_requirements(self.course_key, requirements)
        self.assertEqual(len(get_credit_requirements(self.course_key)), 1)

        requirements = [
            {
                "namespace": "reverification",
                "name": "midterm",
                "criteria": {}
            }
        ]
        set_credit_requirements(self.course_key, requirements)
        self.assertEqual(len(get_credit_requirements(self.course_key)), 1)
        grade_req = CreditRequirement.objects.filter(namespace="grade", name="grade")
        self.assertEqual(len(grade_req), 1)
        self.assertEqual(grade_req[0].active, False)

    def test_requirements_to_disable(self):
        self.add_credit_course()
        requirements = [
            {
                "namespace": "grade",
                "name": "grade",
                "criteria": {
                    "min_grade": 0.8
                }
            },
            {
                "namespace": "grade",
                "name": "grade",
                "criteria": {
                    "min_grade": 0.8
                }
            }
        ]

        set_credit_requirements(self.course_key, requirements)
        old_requirements = CreditRequirement.get_course_requirements(self.course_key)
        self.assertEqual(len(old_requirements), 1)

        requirements = [
            {
                "namespace": "reverification",
                "name": "midterm",
                "criteria": {}
            }
        ]
        requirements_to_disabled = _get_requirements_to_disable(old_requirements, requirements)
        self.assertEqual(len(requirements_to_disabled), 1)
        self.assertEqual(requirements_to_disabled[0], old_requirements[0].id)

        requirements = [
            {
                "namespace": "grade",
                "name": "grade",
                "criteria": {
                    "min_grade": 0.8
                }
            },
            {
                "namespace": "reverification",
                "name": "midterm",
                "criteria": {}
            }
        ]
        requirements_to_disabled = _get_requirements_to_disable(old_requirements, requirements)
        self.assertEqual(len(requirements_to_disabled), 0)

    def add_credit_course(self, enabled=True):
        """ Mark the course as a credit """

        credit_course = CreditCourse(course_key=self.course_key, enabled=enabled)
        credit_course.save()
        return credit_course
