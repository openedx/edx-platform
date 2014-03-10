"""
Tests for class dashboard (Metrics tab in instructor dashboard)
"""

import json

from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from courseware.tests.factories import StudentModuleFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory, AdminFactory
from capa.tests.response_xml_factory import StringResponseXMLFactory

from class_dashboard.dashboard_data import (get_problem_grade_distribution, get_sequential_open_distrib,
                                            get_problem_set_grade_distrib, get_d3_problem_grade_distrib,
                                            get_d3_sequential_open_distrib, get_d3_section_grade_distrib,
                                            get_section_display_name, get_array_section_has_problem
                                            )
from class_dashboard.views import has_instructor_access_for_class

USER_COUNT = 11


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestGetProblemGradeDistribution(ModuleStoreTestCase):
    """
    Tests related to class_dashboard/dashboard_data.py
    """

    def setUp(self):

        self.instructor = AdminFactory.create()
        self.client.login(username=self.instructor.username, password='test')
        self.attempts = 3
        self.course = CourseFactory.create(
            display_name=u"test course omega \u03a9",
        )

        section = ItemFactory.create(
            parent_location=self.course.location,
            category="chapter",
            display_name=u"test factory section omega \u03a9",
        )
        sub_section = ItemFactory.create(
            parent_location=section.location,
            category="sequential",
            display_name=u"test subsection omega \u03a9",
        )

        unit = ItemFactory.create(
            parent_location=sub_section.location,
            category="vertical",
            metadata={'graded': True, 'format': 'Homework'},
            display_name=u"test unit omega \u03a9",
        )

        self.users = [UserFactory.create() for _ in xrange(USER_COUNT)]

        for user in self.users:
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)

        for i in xrange(USER_COUNT - 1):
            category = "problem"
            item = ItemFactory.create(
                parent_location=unit.location,
                category=category,
                data=StringResponseXMLFactory().build_xml(answer='foo'),
                metadata={'rerandomize': 'always'},
                display_name=u"test problem omega \u03a9 " + str(i)
            )

            for j, user in enumerate(self.users):
                StudentModuleFactory.create(
                    grade=1 if i < j else 0,
                    max_grade=1 if i < j else 0.5,
                    student=user,
                    course_id=self.course.id,
                    module_state_key=item.location,
                    state=json.dumps({'attempts': self.attempts}),
                )

            for j, user in enumerate(self.users):
                StudentModuleFactory.create(
                    course_id=self.course.id,
                    module_type='sequential',
                    module_state_key=item.location,
                )

    def test_get_problem_grade_distribution(self):

        prob_grade_distrib = get_problem_grade_distribution(self.course.id)

        for problem in prob_grade_distrib:
            max_grade = prob_grade_distrib[problem]['max_grade']
            self.assertEquals(1, max_grade)

    def test_get_sequential_open_distibution(self):

        sequential_open_distrib = get_sequential_open_distrib(self.course.id)

        for problem in sequential_open_distrib:
            num_students = sequential_open_distrib[problem]
            self.assertEquals(USER_COUNT, num_students)

    def test_get_problemset_grade_distrib(self):

        prob_grade_distrib = get_problem_grade_distribution(self.course.id)
        probset_grade_distrib = get_problem_set_grade_distrib(self.course.id, prob_grade_distrib)

        for problem in probset_grade_distrib:
            max_grade = probset_grade_distrib[problem]['max_grade']
            self.assertEquals(1, max_grade)

            grade_distrib = probset_grade_distrib[problem]['grade_distrib']
            sum_attempts = 0
            for item in grade_distrib:
                sum_attempts += item[1]
            self.assertEquals(USER_COUNT, sum_attempts)

    def test_get_d3_problem_grade_distrib(self):

        d3_data = get_d3_problem_grade_distrib(self.course.id)
        for data in d3_data:
            for stack_data in data['data']:
                sum_values = 0
                for problem in stack_data['stackData']:
                    sum_values += problem['value']
                self.assertEquals(USER_COUNT, sum_values)

    def test_get_d3_sequential_open_distrib(self):

        d3_data = get_d3_sequential_open_distrib(self.course.id)

        for data in d3_data:
            for stack_data in data['data']:
                for problem in stack_data['stackData']:
                    value = problem['value']
                self.assertEquals(0, value)

    def test_get_d3_section_grade_distrib(self):

        d3_data = get_d3_section_grade_distrib(self.course.id, 0)

        for stack_data in d3_data:
            sum_values = 0
            for problem in stack_data['stackData']:
                sum_values += problem['value']
            self.assertEquals(USER_COUNT, sum_values)

    def test_get_section_display_name(self):

        section_display_name = get_section_display_name(self.course.id)
        self.assertMultiLineEqual(section_display_name[0], u"test factory section omega \u03a9")

    def test_get_array_section_has_problem(self):

        b_section_has_problem = get_array_section_has_problem(self.course.id)
        self.assertEquals(b_section_has_problem[0], True)

    def test_dashboard(self):

        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(
            url,
            {
                'idash_mode': 'Metrics'
            }
        )
        self.assertContains(response, '<h2>Course Statistics At A Glance</h2>')

    def test_has_instructor_access_for_class(self):
        """
        Test for instructor access
        """
        ret_val = has_instructor_access_for_class(self.instructor, self.course.id)
        self.assertEquals(ret_val, True)
