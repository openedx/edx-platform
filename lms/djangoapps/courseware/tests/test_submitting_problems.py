'''integration tests for submitting problem responses and getting grades'''

import logging
import json
import time
import random

from urlparse import urlsplit, urlunsplit
from uuid import uuid4

from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import RequestFactory
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

import xmodule.modulestore.django

# Need access to internal func to put users in the right group
from courseware import grades
from courseware.model_data import ModelDataCache
from courseware.access import (has_access, _course_staff_group_name,
                               course_beta_test_group_name)

from student.models import Registration
from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.xml import XMLModuleStore
from mongo_login_helpers import MongoLoginHelpers

#import factories for testing
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from capa.tests.response_xml_factory import OptionResponseXMLFactory

log = logging.getLogger("mitx." + __name__)


def parse_json(response):
    """Parse response, which is assumed to be json"""
    return json.loads(response.content)


def get_user(email):
    '''look up a user by email'''
    return User.objects.get(email=email)


def get_registration(email):
    '''look up registration object by email'''
    return Registration.objects.get(user__email=email)


def mongo_store_config(data_dir):
    '''
    Defines default module store using MongoModuleStore

    Use of this config requires mongo to be running
    '''
    store = {
        'default': {
            'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
            'OPTIONS': {
                'default_class': 'xmodule.raw_module.RawDescriptor',
                'host': 'localhost',
                'db': 'test_xmodule',
                'collection': 'modulestore_%s' % uuid4().hex,
                'fs_root': data_dir,
                'render_template': 'mitxmako.shortcuts.render_to_string',
            }
        }
    }
    store['direct'] = store['default']
    return store

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
TEST_DATA_MONGO_MODULESTORE = mongo_store_config(TEST_DATA_DIR)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestSubmittingProblems(MongoLoginHelpers):
    """Check that a course gets graded properly"""

    # Subclasses should specify the course slug
    course_slug = "UNKNOWN"
    course_when = "UNKNOWN"

    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}

        # Create course
        number = self.course_slug

        self.course = CourseFactory.create(display_name='course_name', number=number)
        assert self.course, "Couldn't load course %r" % course_name

        # create a test student
        self.student = 'view@test.com'
        self.password = 'foo'
        self.create_account('u1', self.student, self.password)
        self.activate_user(self.student)
        self.enroll(self.course)
        self.student_user = get_user(self.student)
        self.factory = RequestFactory()

    def refresh_course(self):
        """re-fetch the course from the database so that the object being dealt with has everything added to it"""
        self.course = modulestore().get_instance(self.course.id, self.course.location)

    def problem_location(self, problem_url_name):
        return "i4x://"+self.course.org+"/{}/problem/{}".format(self.course_slug, problem_url_name)

    def modx_url(self, problem_location, dispatch):
        return reverse(
            'modx_dispatch',
            kwargs={
                'course_id': self.course.id,
                'location': problem_location,
                'dispatch': dispatch,
            }
        )

    def submit_question_answer(self, problem_url_name, responses):
        """
        Submit answers to a question.

        Responses is a dict mapping problem ids (not sure of the right term)
        to answers:
            {'2_1': 'Correct', '2_2': 'Incorrect'}

        """
        problem_location = self.problem_location(problem_url_name)
        modx_url = self.modx_url(problem_location, 'problem_check')

        answer_key_prefix = 'input_i4x-'+self.course.org+'-{}-problem-{}_'.format(self.course_slug, problem_url_name)
        print modx_url
        resp = self.client.post(modx_url, {(answer_key_prefix + k): v for k, v in responses.items()})

        return resp

    def reset_question_answer(self, problem_url_name):
        '''resets specified problem for current user'''
        problem_location = self.problem_location(problem_url_name)
        modx_url = self.modx_url(problem_location, 'problem_reset')
        resp = self.client.post(modx_url)
        return resp

    def add_dropdown_to_section(self, section_location, name, num_inputs=2):
        """create and return problem with two option response inputs (dropdown)"""

        problem_template = "i4x://edx/templates/problem/Blank_Common_Problem"
        prob_xml = OptionResponseXMLFactory().build_xml(
            **{'question_text': 'The correct answer is Correct',
                'num_inputs': num_inputs,
                'weight': num_inputs,
                'options': ['Correct', 'Incorrect'],
                'correct_option': 'Correct'})

        problem = ItemFactory.create(
            parent_location=section_location,
            template=problem_template,
            data=prob_xml,
            metadata={'randomize': 'always'},
            display_name=name
        )

        self.refresh_course()
        return problem

    def add_graded_section_to_course(self, name, format='Homework'):
        """Creates a graded homework section within a chapter and returns the section"""

        #if we don't already have a chapter create a new one
        if not(hasattr(self, 'chapter')):
            self.chapter = ItemFactory.create(
                parent_location=self.course.location,
                template="i4x://edx/templates/chapter/Empty",
            )

        section = ItemFactory.create(
            parent_location=self.chapter.location,
            display_name=name,
            template="i4x://edx/templates/sequential/Empty",
            metadata={'graded': True, 'format': format}
        )
        self.refresh_course()
        return section


class TestCourseGrader(TestSubmittingProblems):
    """Check that a course gets graded properly"""

    course_slug = "graded"
    course_when = "2012_Fall"

    def add_grading_policy(self, grading_policy):
        '''add a grading policy to the course'''
        course_data = {'grading_policy': grading_policy}
        modulestore().update_item(self.course.location, course_data)
        self.refresh_course()

    def get_grade_summary(self):
        '''calls grades.grade for current user and course'''
        model_data_cache = ModelDataCache.cache_for_descriptor_descendents(
            self.course.id, self.student_user, self.course)

        fake_request = self.factory.get(reverse('progress',
                                        kwargs={'course_id': self.course.id}))

        return grades.grade(self.student_user, fake_request,
                            self.course, model_data_cache)

    def get_letter_grade(self):
        '''get the students letter grade'''
        return self.get_grade_summary()['grade']

    def get_homework_scores(self):
        '''get scores for homeworks'''
        return self.get_grade_summary()['totaled_scores']['Homework']

    def get_progress_summary(self):
        '''return progress summary structure for current user and course'''
        model_data_cache = ModelDataCache.cache_for_descriptor_descendents(
            self.course.id, self.student_user, self.course)

        fake_request = self.factory.get(reverse('progress',
                                        kwargs={'course_id': self.course.id}))

        progress_summary = grades.progress_summary(self.student_user,
                                                   fake_request,
                                                   self.course,
                                                   model_data_cache)
        return progress_summary

    def check_grade_percent(self, percent):
        '''assert that percent grade is as expected'''
        grade_summary = self.get_grade_summary()
        self.assertEqual(grade_summary['percent'], percent)

    def check_letter_grade(self, letter):
        '''assert letter grade is as expected'''
        self.assertEqual(self.get_letter_grade(), letter)

    def earned_hw_scores(self):
        """Global scores, each Score is a Problem Set"""
        return [s.earned for s in self.get_homework_scores()]

    def score_for_hw(self, hw_url_name):
        """returns list of scores for a given url"""
        hw_section = [section for section
                      in self.get_progress_summary()[0]['sections']
                      if section.get('url_name') == hw_url_name][0]
        return [s.earned for s in hw_section['scores']]

    def basic_setup(self):
        '''set up a simple course for testing basic grading functionality'''
        grading_policy = {
            "GRADER": [{
                "type": "Homework",
                "min_count": 1,
                "drop_count": 0,
                "short_label": "HW",
                "weight": 1.0
            }],
            "GRADE_CUTOFFS": {
            'A': .9,
            'B': .33
            }
        }
        self.add_grading_policy(grading_policy)

        #set up a simple course with four problems
        self.homework = self.add_graded_section_to_course('homework')
        self.p1 = self.add_dropdown_to_section(self.homework.location, 'p1', 1)
        self.p2 = self.add_dropdown_to_section(self.homework.location, 'p2', 1)
        self.p3 = self.add_dropdown_to_section(self.homework.location, 'p3', 1)
        self.refresh_course()

    def test_None_grade(self):
        '''check grade is 0 to begin'''
        self.basic_setup()
        self.check_grade_percent(0)
        self.check_letter_grade(None)

    def test_B_grade_exact(self):
        '''check that at exactly the cutoff, the grade is B'''
        self.basic_setup()
        self.submit_question_answer('p1', {'2_1': 'Correct'})
        self.check_grade_percent(0.33)
        self.check_letter_grade('B')

    def test_B_grade_above(self):
        '''check grade between cutoffs'''
        self.basic_setup()
        self.submit_question_answer('p1', {'2_1': 'Correct'})
        self.submit_question_answer('p2', {'2_1': 'Correct'})
        self.check_grade_percent(0.67)
        self.check_letter_grade('B')

    def test_A_grade(self):
        '''check that 100% comlpetion gets an A'''
        self.basic_setup()
        self.submit_question_answer('p1', {'2_1': 'Correct'})
        self.submit_question_answer('p2', {'2_1': 'Correct'})
        self.submit_question_answer('p3', {'2_1': 'Correct'})
        self.check_grade_percent(1.0)
        self.check_letter_grade('A')

    def test_weighted_grading(self):
        '''Set up a simple course for testing weighted grading functionality'''
        grading_policy = {
            "GRADER": [
            {
                "type": "Homework",
                "min_count": 1,
                "drop_count": 0,
                "short_label": "HW",
                "weight": 0.25
            },
                {
                    "type": "Final",
                    "name": "Final Section",
                    "short_label": "Final",
                    "weight": 0.75
                }]
        }
        self.add_grading_policy(grading_policy)

        #set up a structure of 1 homework and 1 final
        self.homework = self.add_graded_section_to_course('homework')
        self.problem = self.add_dropdown_to_section(self.homework.location, 'H1P1')
        self.final = self.add_graded_section_to_course('Final Section', 'Final')
        self.final_question = self.add_dropdown_to_section(self.final.location, 'FinalQuestion')

        # Only get half of the first problem correct
        self.submit_question_answer('H1P1', {'2_1': 'Correct', '2_2': 'Incorrect'})
        self.check_grade_percent(0.13)
        self.assertEqual(self.earned_hw_scores(), [1.0])   # Order matters
        self.assertEqual(self.score_for_hw('homework'), [1.0])

        # Get both parts correct
        self.submit_question_answer('H1P1', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(0.25)
        self.assertEqual(self.earned_hw_scores(), [2.0])   # Order matters
        self.assertEqual(self.score_for_hw('homework'), [2.0])

        # Do the final
        # Now we answer the final question (worth 75% of the grade)
        self.submit_question_answer('FinalQuestion', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(1.0)   # Hooray! We got 100%

    def test_dropping_homework(self):
        '''Set up a simple course for testing the dropping grading functionality'''
        grading_policy = {
            "GRADER": [
            {
                "type": "Homework",
                "min_count": 3,
                "drop_count": 1,
                "short_label": "HW",
                "weight": 1
            }]
        }
        self.add_grading_policy(grading_policy)

        # Set up a course structure that just consists of 3 homeworks.
        # Since the grading policy drops 1, each problem is worth 25%
        self.homework1 = self.add_graded_section_to_course('homework1')
        self.h1p1 = self.add_dropdown_to_section(self.homework1.location, 'H1P1', 1)
        self.h1p2 = self.add_dropdown_to_section(self.homework1.location, 'H1P2', 1)
        self.homework2 = self.add_graded_section_to_course('homework2')
        self.h1p1 = self.add_dropdown_to_section(self.homework2.location, 'H2P1', 1)
        self.h1p2 = self.add_dropdown_to_section(self.homework2.location, 'H2P2', 1)
        self.homework3 = self.add_graded_section_to_course('homework3')
        self.h3p1 = self.add_dropdown_to_section(self.homework3.location, 'H3P1', 1)
        self.h3p2 = self.add_dropdown_to_section(self.homework3.location, 'H3P2', 1)

        #Get The first problem correct
        self.submit_question_answer('H1P1', {'2_1': 'Correct'})
        self.check_grade_percent(0.25)
        self.assertEqual(self.earned_hw_scores(), [1.0, 0, 0])   # Order matters
        self.assertEqual(self.score_for_hw('homework1'), [1.0, 0.0])
        self.check_letter_grade(None)

        #Get the second problem incorrect
        self.submit_question_answer('H1P2', {'2_1': 'Incorrect'})
        self.check_grade_percent(0.25)
        self.assertEqual(self.earned_hw_scores(), [1.0, 0, 0])   # Order matters
        self.assertEqual(self.score_for_hw('homework1'), [1.0, 0.0])
        self.check_letter_grade(None)

        #Get Homework2 correct
        self.submit_question_answer('H2P1', {'2_1': 'Correct'})
        self.submit_question_answer('H2P2', {'2_1': 'Correct'})
        self.check_grade_percent(0.75)
        self.assertEqual(self.earned_hw_scores(), [1.0, 2.0, 0])   # Order matters
        self.assertEqual(self.score_for_hw('homework2'), [1.0, 1.0])
        self.check_letter_grade('Pass')

        #Get homework3 half correct, shouldn't change grade
        self.submit_question_answer('H3P1', {'2_1': 'Correct'})
        self.check_grade_percent(0.75)
        self.assertEqual(self.earned_hw_scores(), [1.0, 2.0, 1.0])   # Order matters
        self.assertEqual(self.score_for_hw('homework3'), [1.0, 0.0])
        self.check_letter_grade('Pass')

        #get all of homework3 correct, which hsould replace homework 1
        self.submit_question_answer('H3P2', {'2_1': 'Correct'})
        self.check_grade_percent(1.0)
        self.assertEqual(self.earned_hw_scores(), [1.0, 2.0, 2.0])   # Order matters
        self.assertEqual(self.score_for_hw('homework3'), [1.0, 1.0])
        self.check_letter_grade('Pass')


class TestPythonGradedResponse(TestSubmittingProblems):
    """Check that we can submit a schematic response and custom response, and it answers properly."""

    course_slug = "embedded_python"
    course_when = "2013_Spring"

    def setUp(self):
        super(TestPythonGradedResponse, self).setUp()
        self.section = self.add_graded_section_to_course('section')
        self.correct_responses = {}
        self.incorrect_responses = {}

    def schematic_setup(self, name):
        '''set up an example Circuit_Schematic_Builder problem'''

        from capa.tests.response_xml_factory import SchematicResponseXMLFactory
        schematic_template = "i4x://edx/templates/problem/Circuit_Schematic_Builder"
        script = """# for a schematic response, submission[i] is the json representation
# of the diagram and analysis results for the i-th schematic tag

def get_tran(json,signal):
  for element in json:
    if element[0] == 'transient':
      return element[1].get(signal,[])
  return []

def get_value(at,output):
  for (t,v) in output:
    if at == t: return v
  return None

output = get_tran(submission[0],'Z')
okay = True

# output should be 1, 1, 1, 1, 1, 0, 0, 0
if get_value(0.0000004,output) < 2.7: okay = False;
if get_value(0.0000009,output) < 2.7: okay = False;
if get_value(0.0000014,output) < 2.7: okay = False;
if get_value(0.0000019,output) < 2.7: okay = False;
if get_value(0.0000024,output) < 2.7: okay = False;
if get_value(0.0000029,output) > 0.25: okay = False;
if get_value(0.0000034,output) > 0.25: okay = False;
if get_value(0.0000039,output) > 0.25: okay = False;

correct = ['correct' if okay else 'incorrect']"""
        xmldata = SchematicResponseXMLFactory().build_xml(answer=script)
        problem = ItemFactory.create(
            parent_location=self.section.location,
            template=schematic_template,
            display_name=name,
            data=xmldata
        )

                #define the correct and incorrect responses to this problem
        self.correct_responses[name] = json.dumps(
            [['transient', {'Z': [
                [0.0000004, 2.8],
                [0.0000009, 2.8],
                [0.0000014, 2.8],
                [0.0000019, 2.8],
                [0.0000024, 2.8],
                [0.0000029, 0.2],
                [0.0000034, 0.2],
                [0.0000039, 0.2]
            ]}]]
        )

        self.incorrect_responses[name] = json.dumps(
            [['transient', {'Z': [
                [0.0000004, 2.8],
                [0.0000009, 0.0],  # wrong.
                [0.0000014, 2.8],
                [0.0000019, 2.8],
                [0.0000024, 2.8],
                [0.0000029, 0.2],
                [0.0000034, 0.2],
                [0.0000039, 0.2]
            ]}]]
        )

        self.refresh_course()

    def costum_response_setup(self, name):
        '''set up an example custom response problem using a check function'''

        from capa.tests.response_xml_factory import CustomResponseXMLFactory
        custom_template = "i4x://edx/templates/problem/Custom_Python-Evaluated_Input"
        test_csv = """def test_csv(expect, ans):
   # Take out all spaces in expected answer
   expect = [i.strip(' ') for i in str(expect).split(',')]
   # Take out all spaces in student solution
   ans = [i.strip(' ') for i in str(ans).split(',')]

   def strip_q(x):
      # Strip quotes around strings if students have entered them
      stripped_ans = []
      for item in x:
         if item[0] == "'" and item[-1]=="'":
            item = item.strip("'")
         elif item[0] == '"' and item[-1] == '"':
            item = item.strip('"')
         stripped_ans.append(item)
      return stripped_ans

   return strip_q(expect) == strip_q(ans)"""
        expect = "0, 1, 2, 3, 4, 5, 'Outside of loop', 6"
        cfn_problem_xml = CustomResponseXMLFactory().build_xml(script=test_csv, cfn='test_csv', expect=expect)

        problem = ItemFactory.create(
            parent_location=self.section.location,
            template=custom_template,
            data=cfn_problem_xml,
            display_name=name
        )

        self.correct_responses[name] = expect
        self.incorrect_responses[name] = 'Xyzzy'

        self.refresh_course()
        return problem

    def computed_answer_setup(self, name):
        '''set up an example problem using an answer script'''

        script = """if submission[0] == "Xyzzy":
    correct = ['correct']
else:
    correct = ['incorrect']"""

        from capa.tests.response_xml_factory import CustomResponseXMLFactory
        custom_template = "i4x://edx/templates/problem/Custom_Python-Evaluated_Input"

        computed_xml = CustomResponseXMLFactory().build_xml(answer=script)

        problem = ItemFactory.create(
            parent_location=self.section.location,
            template=custom_template,
            data=computed_xml,
            display_name=name
        )

        self.correct_responses[name] = 'Xyzzy'
        self.incorrect_responses[name] = "No!"

        self.refresh_course()
        return problem

    def check_correct(self, name):
        '''check that problem named "name" gets evaluated correctly correctly'''
        resp = self.submit_question_answer(name, {'2_1': self.correct_responses[name]})

        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'correct')

    def check_incorrect(self, name):
        '''check that problem named "name" gets evaluated correctly correctly'''
        resp = self.submit_question_answer(name, {'2_1': self.incorrect_responses[name]})

        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'incorrect')

    def check_reset(self, name):
        '''check that the problem can be reset'''
        #first, get the question wrong
        resp = self.submit_question_answer(name, {'2_1': self.incorrect_responses[name]})
        #reset the question
        self.reset_question_answer(name)
        #then get it right
        resp = self.submit_question_answer(name, {'2_1': self.correct_responses[name]})

        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'correct')


    def test_schematic_correct(self):
        name = "schematic_problem"
        self.schematic_setup(name)
        self.check_correct(name)

    def test_schematic_incorrect(self):
        name = "schematic_problem"
        self.schematic_setup(name)
        self.check_incorrect(name)

    def test_schematic_reset(self):
        name = "schematic_problem"
        self.schematic_setup(name)
        self.check_reset(name)

    def test_check_function_correct(self):
        name = 'cfn_problem'
        self.costum_response_setup(name)
        self.check_correct(name)

    def test_check_function_incorrect(self):
        name = 'cfn_problem'
        self.costum_response_setup(name)
        self.check_incorrect(name)

    def test_check_function_reset(self):
        name = 'cfn_problem'
        self.costum_response_setup(name)
        self.check_reset(name)

    def test_computed_correct(self):
        name = 'computed_answer'
        self.computed_answer_setup(name)
        self.check_correct(name)

    def test_computed_incorrect(self):
        name = 'computed_answer'
        self.computed_answer_setup(name)
        self.check_incorrect(name)

    def test_computed_reset(self):
        name = 'computed_answer'
        self.computed_answer_setup(name)
        self.check_reset(name)
