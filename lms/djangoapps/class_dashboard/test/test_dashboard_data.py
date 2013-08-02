

from mock import Mock, patch
import json

from django.test.utils import override_settings
from django.test import TestCase
from django.core import management

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from courseware.tests.factories import StudentModuleFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from courseware.models import StudentModule
from capa.tests.response_xml_factory import StringResponseXMLFactory
from xmodule.modulestore import Location
from queryable_student_module.management.commands import populate_studentmoduleexpand

from xmodule.course_module import CourseDescriptor

from class_dashboard.dashboard_data import get_problem_grade_distribution, get_problem_attempt_distrib, get_sequential_open_distrib, \
                                           get_last_populate, get_problem_set_grade_distribution, get_d3_problem_grade_distribution, \
                                           get_d3_problem_attempt_distribution, get_d3_sequential_open_distribution, \
                                           get_d3_section_grade_distribution, get_section_display_name, get_array_section_has_problem

USER_COUNT = 11

@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestGetProblemGradeDistribution(ModuleStoreTestCase):
    """
    Tests needed:
      - simple test, make sure output correct
      - test when a problem has two max_grade's, should just take the larger value
    """
    
    def setUp(self):
        
        self.command = 'populate_studentmoduleexpand'
        self.script_id = "studentmoduleexpand"
        self.attempts = 3
        
        self.course = CourseFactory.create()
        
        section = ItemFactory.create(
            parent_location=self.course.location,
            category="chapter",
            display_name="test factory section",
        )
        sub_section = ItemFactory.create(
            parent_location=section.location,
            category="sequential",
           # metadata={'graded': True, 'format': 'Homework'}
        )
    
        unit = ItemFactory.create(
            parent_location=sub_section.location,
            category="vertical",
            metadata={'graded': True, 'format': 'Homework'}
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
                metadata={'rerandomize': 'always'}
            )
    
            for j, user in enumerate(self.users):
                StudentModuleFactory.create(
                    grade=1 if i < j else 0,
                    max_grade=1 if i< j else 0.5,
                    student=user,
                    course_id=self.course.id,
                    module_state_key=Location(item.location).url(),
                    state=json.dumps({'attempts': self.attempts}),
                )

            for j, user in enumerate(self.users):
                StudentModuleFactory.create(
                    course_id=self.course.id,
                    module_type='sequential',
                    module_state_key=Location(item.location).url(),
                )

    def test_get_problem_grade_distribution(self):

        prob_grade_distrib = get_problem_grade_distribution(self.course.id)

        for problem in prob_grade_distrib:
            max_grade = prob_grade_distrib[problem]['max_grade']
            self.assertEquals(1, max_grade)


    def test_get_problem_attempt_distribution(self):
 
        # Call command
        management.call_command(self.command, self.course.id)
        prob_attempts_distrib = get_problem_attempt_distrib(self.course.id)
        
        for problem in prob_attempts_distrib:
            num_attempts = prob_attempts_distrib[problem][self.attempts -1]
            self.assertEquals(USER_COUNT, num_attempts)


    def test_get_sequential_open_distibution(self):
        
        sequential_open_distrib = get_sequential_open_distrib(self.course.id)
        
        for problem in sequential_open_distrib:
            num_students = sequential_open_distrib[problem]
            self.assertEquals(USER_COUNT, num_students)
 

    def test_get_last_populate(self):
        
        timestamp = get_last_populate(self.course.id, self.script_id)
        self.assertEquals(timestamp, None)
        
        management.call_command(self.command, self.course.id)
        timestamp = get_last_populate(self.course.id, self.script_id)
        self.assertNotEquals(timestamp, None)


    def test_get_problemset_grade_distrib(self):

        prob_grade_distrib = get_problem_grade_distribution(self.course.id)
        probset_grade_distrib = get_problem_set_grade_distribution(self.course.id, prob_grade_distrib)

        for problem in probset_grade_distrib:
            max_grade = probset_grade_distrib[problem]['max_grade']
            self.assertEquals(1, max_grade)

            grade_distrib = probset_grade_distrib[problem]['grade_distrib']
            sum_attempts = 0
            for item in grade_distrib:
                sum_attempts += item[1]
            self.assertEquals(USER_COUNT, sum_attempts)


  #  @patch('class_dashboard.dashboard_data.get_problem_grade_distribution')
    def test_get_d3_problem_grade_distrib(self): #, mock_get_data):
        
        d3_data = get_d3_problem_grade_distribution(self.course.id)
        for data in d3_data:
            for stack_data in data['data']:
                sum_values = 0
                for problem in stack_data['stackData']:
                    sum_values += problem['value']
                self.assertEquals(USER_COUNT, sum_values)


    def test_get_d3_problem_attempt_distrib(self):
        
        # Call command
        management.call_command(self.command, self.course.id)
        d3_data = get_d3_problem_attempt_distribution(self.course.id)
        
        for data in d3_data:
            for stack_data in data['data']:
                sum_values = 0
                for problem in stack_data['stackData']:
                    sum_values += problem['value']
                self.assertEquals(USER_COUNT, sum_values)   


    def test_get_d3_sequential_open_distrib(self):
        
        d3_data = get_d3_sequential_open_distribution(self.course.id)
        
        for data in d3_data:
            for stack_data in data['data']:
                for problem in stack_data['stackData']:
                    value = problem['value']
                self.assertEquals(0, value)   


    def test_get_d3_section_grade_distrib(self):


        d3_data = get_d3_section_grade_distribution(self.course.id, 0)
        
        for stack_data in d3_data:
            sum_values = 0
            for problem in stack_data['stackData']:
                sum_values += problem['value']
            self.assertEquals(USER_COUNT, sum_values)


    def test_get_section_display_name(self):
        
        section_display_name = get_section_display_name(self.course.id)
        
        self.assertMultiLineEqual(section_display_name[0], 'test factory section')


    def test_get_array_section_has_problem(self):
        
        b_section_has_problem = get_array_section_has_problem(self.course.id)
        
        print b_section_has_problem
        self.assertEquals(b_section_has_problem[0], True)
