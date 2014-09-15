# -*- coding: utf-8 -*-
"""
Integration tests for submitting problem responses and getting grades.
"""
# text processing dependencies
import json
import os
from textwrap import dedent

from mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

# Need access to internal func to put users in the right group
from courseware import grades
from courseware.models import StudentModule

#import factories and parent testcase modules
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from capa.tests.response_xml_factory import (
    OptionResponseXMLFactory, CustomResponseXMLFactory, SchematicResponseXMLFactory,
    CodeResponseXMLFactory,
)
from courseware.tests.helpers import LoginEnrollmentTestCase
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from lms.lib.xblock.runtime import quote_slashes
from student.tests.factories import UserFactory


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestSubmittingProblems(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
        Check that a course gets graded properly.
    """

    # arbitrary constant
    COURSE_SLUG = "100"
    COURSE_NAME = "test_course"

    def setUp(self):

        super(TestSubmittingProblems, self).setUp(create_user=False)
        # Create course
        self.course = CourseFactory.create(display_name=self.COURSE_NAME, number=self.COURSE_SLUG)
        assert self.course, "Couldn't load course %r" % self.COURSE_NAME

        # create a test student
        self.student = 'view@test.com'
        self.password = 'foo'
        self.create_account('u1', self.student, self.password)
        self.activate_user(self.student)
        self.enroll(self.course)
        self.student_user = User.objects.get(email=self.student)
        self.factory = RequestFactory()

    def refresh_course(self):
        """
        Re-fetch the course from the database so that the object being dealt with has everything added to it.
        """
        self.course = self.store.get_course(self.course.id)

    def problem_location(self, problem_url_name):
        """
        Returns the url of the problem given the problem's name
        """

        return self.course.id.make_usage_key('problem', problem_url_name)

    def modx_url(self, problem_location, dispatch):
        """
        Return the url needed for the desired action.

        problem_location: location of the problem on which we want some action

        dispatch: the the action string that gets passed to the view as a kwarg
            example: 'check_problem' for having responses processed
        """
        return reverse(
            'xblock_handler',
            kwargs={
                'course_id': self.course.id.to_deprecated_string(),
                'usage_id': quote_slashes(problem_location.to_deprecated_string()),
                'handler': 'xmodule_handler',
                'suffix': dispatch,
            }
        )

    def submit_question_answer(self, problem_url_name, responses):
        """
        Submit answers to a question.

        Responses is a dict mapping problem ids to answers:
            {'2_1': 'Correct', '2_2': 'Incorrect'}
        """

        problem_location = self.problem_location(problem_url_name)
        modx_url = self.modx_url(problem_location, 'problem_check')

        answer_key_prefix = 'input_i4x-{}-{}-problem-{}_'.format(
            self.course.org, self.course.id.course, problem_url_name
        )

        # format the response dictionary to be sent in the post request by adding the above prefix to each key
        response_dict = {(answer_key_prefix + k): v for k, v in responses.items()}
        resp = self.client.post(modx_url, response_dict)

        return resp

    def reset_question_answer(self, problem_url_name):
        """
        Reset specified problem for current user.
        """
        problem_location = self.problem_location(problem_url_name)
        modx_url = self.modx_url(problem_location, 'problem_reset')
        resp = self.client.post(modx_url)
        return resp

    def show_question_answer(self, problem_url_name):
        """
        Shows the answer to the current student.
        """
        problem_location = self.problem_location(problem_url_name)
        modx_url = self.modx_url(problem_location, 'problem_show')
        resp = self.client.post(modx_url)
        return resp

    def add_dropdown_to_section(self, section_location, name, num_inputs=2):
        """
        Create and return a dropdown problem.

        section_location: location object of section in which to create the problem
            (problems must live in a section to be graded properly)

        name: string name of the problem

        num_input: the number of input fields to create in the problem
        """

        prob_xml = OptionResponseXMLFactory().build_xml(
            question_text='The correct answer is Correct',
            num_inputs=num_inputs,
            weight=num_inputs,
            options=['Correct', 'Incorrect', u'ⓤⓝⓘⓒⓞⓓⓔ'],
            correct_option='Correct'
        )

        problem = ItemFactory.create(
            parent_location=section_location,
            category='problem',
            data=prob_xml,
            metadata={'rerandomize': 'always'},
            display_name=name
        )

        # re-fetch the course from the database so the object is up to date
        self.refresh_course()
        return problem

    def add_graded_section_to_course(self, name, section_format='Homework', late=False, reset=False, showanswer=False):
        """
        Creates a graded homework section within a chapter and returns the section.
        """

        # if we don't already have a chapter create a new one
        if not(hasattr(self, 'chapter')):
            self.chapter = ItemFactory.create(
                parent_location=self.course.location,
                category='chapter'
            )

        if late:
            section = ItemFactory.create(
                parent_location=self.chapter.location,
                display_name=name,
                category='sequential',
                metadata={'graded': True, 'format': section_format, 'due': '2013-05-20T23:30'}
            )
        elif reset:
            section = ItemFactory.create(
                parent_location=self.chapter.location,
                display_name=name,
                category='sequential',
                rerandomize='always',
                metadata={
                    'graded': True,
                    'format': section_format,
                }
            )

        elif showanswer:
            section = ItemFactory.create(
                parent_location=self.chapter.location,
                display_name=name,
                category='sequential',
                showanswer='never',
                metadata={
                    'graded': True,
                    'format': section_format,
                }
            )

        else:
            section = ItemFactory.create(
                parent_location=self.chapter.location,
                display_name=name,
                category='sequential',
                metadata={'graded': True, 'format': section_format}
            )

        # now that we've added the problem and section to the course
        # we fetch the course from the database so the object we are
        # dealing with has these additions
        self.refresh_course()
        return section


class TestCourseGrader(TestSubmittingProblems):
    """
    Suite of tests for the course grader.
    """

    def add_grading_policy(self, grading_policy):
        """
        Add a grading policy to the course.
        """

        self.course.grading_policy = grading_policy
        self.update_course(self.course, self.student_user.id)
        self.refresh_course()

    def get_grade_summary(self):
        """
        calls grades.grade for current user and course.

        the keywords for the returned object are
        - grade : A final letter grade.
        - percent : The final percent for the class (rounded up).
        - section_breakdown : A breakdown of each section that makes
            up the grade. (For display)
        - grade_breakdown : A breakdown of the major components that
            make up the final grade. (For display)
        """

        fake_request = self.factory.get(
            reverse('progress', kwargs={'course_id': self.course.id.to_deprecated_string()})
        )

        return grades.grade(self.student_user, fake_request, self.course)

    def get_progress_summary(self):
        """
        Return progress summary structure for current user and course.

        Returns
        - courseware_summary is a summary of all sections with problems in the course.
        It is organized as an array of chapters, each containing an array of sections,
        each containing an array of scores. This contains information for graded and
        ungraded problems, and is good for displaying a course summary with due dates,
        etc.
        """

        fake_request = self.factory.get(
            reverse('progress', kwargs={'course_id': self.course.id.to_deprecated_string()})
        )

        progress_summary = grades.progress_summary(
            self.student_user, fake_request, self.course
        )
        return progress_summary

    def check_grade_percent(self, percent):
        """
        Assert that percent grade is as expected.
        """
        grade_summary = self.get_grade_summary()
        self.assertEqual(grade_summary['percent'], percent)

    def earned_hw_scores(self):
        """
        Global scores, each Score is a Problem Set.

        Returns list of scores: [<points on hw_1>, <poinst on hw_2>, ..., <poinst on hw_n>]
        """
        return [s.earned for s in self.get_grade_summary()['totaled_scores']['Homework']]

    def score_for_hw(self, hw_url_name):
        """
        Returns list of scores for a given url.

        Returns list of scores for the given homework:
            [<points on problem_1>, <poinst on problem_2>, ..., <poinst on problem_n>]
        """

        # list of grade summaries for each section
        sections_list = []
        for chapter in self.get_progress_summary():
            sections_list.extend(chapter['sections'])

        # get the first section that matches the url (there should only be one)
        hw_section = next(section for section in sections_list if section.get('url_name') == hw_url_name)
        return [s.earned for s in hw_section['scores']]

    def basic_setup(self, late=False, reset=False, showanswer=False):
        """
        Set up a simple course for testing basic grading functionality.
        """

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

        # set up a simple course with four problems
        self.homework = self.add_graded_section_to_course('homework', late=late, reset=reset, showanswer=showanswer)
        self.add_dropdown_to_section(self.homework.location, 'p1', 1)
        self.add_dropdown_to_section(self.homework.location, 'p2', 1)
        self.add_dropdown_to_section(self.homework.location, 'p3', 1)
        self.refresh_course()

    def weighted_setup(self):
        """
        Set up a simple course for testing weighted grading functionality.
        """

        grading_policy = {
            "GRADER": [{
                "type": "Homework",
                "min_count": 1,
                "drop_count": 0,
                "short_label": "HW",
                "weight": 0.25
            }, {
                "type": "Final",
                "name": "Final Section",
                "short_label": "Final",
                "weight": 0.75
            }]
        }
        self.add_grading_policy(grading_policy)

        # set up a structure of 1 homework and 1 final
        self.homework = self.add_graded_section_to_course('homework')
        self.problem = self.add_dropdown_to_section(self.homework.location, 'H1P1')
        self.final = self.add_graded_section_to_course('Final Section', 'Final')
        self.final_question = self.add_dropdown_to_section(self.final.location, 'FinalQuestion')

    def dropping_setup(self):
        """
        Set up a simple course for testing the dropping grading functionality.
        """

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
        # Since the grading policy drops 1 entire homework, each problem is worth 25%

        # names for the problem in the homeworks
        self.hw1_names = ['h1p1', 'h1p2']
        self.hw2_names = ['h2p1', 'h2p2']
        self.hw3_names = ['h3p1', 'h3p2']

        self.homework1 = self.add_graded_section_to_course('homework1')
        self.add_dropdown_to_section(self.homework1.location, self.hw1_names[0], 1)
        self.add_dropdown_to_section(self.homework1.location, self.hw1_names[1], 1)
        self.homework2 = self.add_graded_section_to_course('homework2')
        self.add_dropdown_to_section(self.homework2.location, self.hw2_names[0], 1)
        self.add_dropdown_to_section(self.homework2.location, self.hw2_names[1], 1)
        self.homework3 = self.add_graded_section_to_course('homework3')
        self.add_dropdown_to_section(self.homework3.location, self.hw3_names[0], 1)
        self.add_dropdown_to_section(self.homework3.location, self.hw3_names[1], 1)

    def test_submission_late(self):
        """Test problem for due date in the past"""
        self.basic_setup(late=True)
        resp = self.submit_question_answer('p1', {'2_1': 'Correct'})
        self.assertEqual(resp.status_code, 200)
        err_msg = (
            "The state of this problem has changed since you loaded this page. "
            "Please refresh your page."
        )
        self.assertEqual(json.loads(resp.content).get("success"), err_msg)

    def test_submission_reset(self):
        """Test problem ProcessingErrors due to resets"""
        self.basic_setup(reset=True)
        resp = self.submit_question_answer('p1', {'2_1': 'Correct'})
        #  submit a second time to draw NotFoundError
        resp = self.submit_question_answer('p1', {'2_1': 'Correct'})
        self.assertEqual(resp.status_code, 200)
        err_msg = (
            "The state of this problem has changed since you loaded this page. "
            "Please refresh your page."
        )
        self.assertEqual(json.loads(resp.content).get("success"), err_msg)

    def test_submission_show_answer(self):
        """Test problem for ProcessingErrors due to showing answer"""
        self.basic_setup(showanswer=True)
        resp = self.show_question_answer('p1')
        self.assertEqual(resp.status_code, 200)
        err_msg = (
            "The state of this problem has changed since you loaded this page. "
            "Please refresh your page."
        )
        self.assertEqual(json.loads(resp.content).get("success"), err_msg)

    def test_none_grade(self):
        """
        Check grade is 0 to begin with.
        """
        self.basic_setup()
        self.check_grade_percent(0)
        self.assertEqual(self.get_grade_summary()['grade'], None)

    def test_b_grade_exact(self):
        """
        Check that at exactly the cutoff, the grade is B.
        """
        self.basic_setup()
        self.submit_question_answer('p1', {'2_1': 'Correct'})
        self.check_grade_percent(0.33)
        self.assertEqual(self.get_grade_summary()['grade'], 'B')

    def test_b_grade_above(self):
        """
        Check grade between cutoffs.
        """
        self.basic_setup()
        self.submit_question_answer('p1', {'2_1': 'Correct'})
        self.submit_question_answer('p2', {'2_1': 'Correct'})
        self.check_grade_percent(0.67)
        self.assertEqual(self.get_grade_summary()['grade'], 'B')

    def test_a_grade(self):
        """
        Check that 100 percent completion gets an A
        """
        self.basic_setup()
        self.submit_question_answer('p1', {'2_1': 'Correct'})
        self.submit_question_answer('p2', {'2_1': 'Correct'})
        self.submit_question_answer('p3', {'2_1': 'Correct'})
        self.check_grade_percent(1.0)
        self.assertEqual(self.get_grade_summary()['grade'], 'A')

    def test_wrong_answers(self):
        """
        Check that answering incorrectly is graded properly.
        """
        self.basic_setup()
        self.submit_question_answer('p1', {'2_1': 'Correct'})
        self.submit_question_answer('p2', {'2_1': 'Correct'})
        self.submit_question_answer('p3', {'2_1': 'Incorrect'})
        self.check_grade_percent(0.67)
        self.assertEqual(self.get_grade_summary()['grade'], 'B')

    def test_submissions_api_overrides_scores(self):
        """
        Check that answering incorrectly is graded properly.
        """
        self.basic_setup()
        self.submit_question_answer('p1', {'2_1': 'Correct'})
        self.submit_question_answer('p2', {'2_1': 'Correct'})
        self.submit_question_answer('p3', {'2_1': 'Incorrect'})
        self.check_grade_percent(0.67)
        self.assertEqual(self.get_grade_summary()['grade'], 'B')

        # But now we mock out a get_scores call, and watch as it overrides the
        # score read from StudentModule and our student gets an A instead.
        with patch('submissions.api.get_scores') as mock_get_scores:
            mock_get_scores.return_value = {
                self.problem_location('p3').to_deprecated_string(): (1, 1)
            }
            self.check_grade_percent(1.0)
            self.assertEqual(self.get_grade_summary()['grade'], 'A')

    def test_submissions_api_anonymous_student_id(self):
        """
        Check that the submissions API is sent an anonymous student ID.
        """
        self.basic_setup()
        self.submit_question_answer('p1', {'2_1': 'Correct'})
        self.submit_question_answer('p2', {'2_1': 'Correct'})
        self.submit_question_answer('p3', {'2_1': 'Incorrect'})

        with patch('submissions.api.get_scores') as mock_get_scores:
            mock_get_scores.return_value = {
                self.problem_location('p3').to_deprecated_string(): (1, 1)
            }
            self.get_grade_summary()

            # Verify that the submissions API was sent an anonymized student ID
            mock_get_scores.assert_called_with(
                self.course.id.to_deprecated_string(), '99ac6730dc5f900d69fd735975243b31'
            )

    def test_weighted_homework(self):
        """
        Test that the homework section has proper weight.
        """
        self.weighted_setup()

        # Get both parts correct
        self.submit_question_answer('H1P1', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(0.25)
        self.assertEqual(self.earned_hw_scores(), [2.0])  # Order matters
        self.assertEqual(self.score_for_hw('homework'), [2.0])

    def test_weighted_exam(self):
        """
        Test that the exam section has the proper weight.
        """
        self.weighted_setup()
        self.submit_question_answer('FinalQuestion', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(0.75)

    def test_weighted_total(self):
        """
        Test that the weighted total adds to 100.
        """
        self.weighted_setup()
        self.submit_question_answer('H1P1', {'2_1': 'Correct', '2_2': 'Correct'})
        self.submit_question_answer('FinalQuestion', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(1.0)

    def dropping_homework_stage1(self):
        """
        Get half the first homework correct and all of the second
        """
        self.submit_question_answer(self.hw1_names[0], {'2_1': 'Correct'})
        self.submit_question_answer(self.hw1_names[1], {'2_1': 'Incorrect'})
        for name in self.hw2_names:
            self.submit_question_answer(name, {'2_1': 'Correct'})

    def test_dropping_grades_normally(self):
        """
        Test that the dropping policy does not change things before it should.
        """
        self.dropping_setup()
        self.dropping_homework_stage1()

        self.assertEqual(self.score_for_hw('homework1'), [1.0, 0.0])
        self.assertEqual(self.score_for_hw('homework2'), [1.0, 1.0])
        self.assertEqual(self.earned_hw_scores(), [1.0, 2.0, 0])  # Order matters
        self.check_grade_percent(0.75)

    def test_dropping_nochange(self):
        """
        Tests that grade does not change when making the global homework grade minimum not unique.
        """
        self.dropping_setup()
        self.dropping_homework_stage1()
        self.submit_question_answer(self.hw3_names[0], {'2_1': 'Correct'})

        self.assertEqual(self.score_for_hw('homework1'), [1.0, 0.0])
        self.assertEqual(self.score_for_hw('homework2'), [1.0, 1.0])
        self.assertEqual(self.score_for_hw('homework3'), [1.0, 0.0])
        self.assertEqual(self.earned_hw_scores(), [1.0, 2.0, 1.0])  # Order matters
        self.check_grade_percent(0.75)

    def test_dropping_all_correct(self):
        """
        Test that the lowest is dropped for a perfect score.
        """
        self.dropping_setup()

        self.dropping_homework_stage1()
        for name in self.hw3_names:
            self.submit_question_answer(name, {'2_1': 'Correct'})

        self.check_grade_percent(1.0)
        self.assertEqual(self.earned_hw_scores(), [1.0, 2.0, 2.0])  # Order matters
        self.assertEqual(self.score_for_hw('homework3'), [1.0, 1.0])


class ProblemWithUploadedFilesTest(TestSubmittingProblems):
    """Tests of problems with uploaded files."""

    def setUp(self):
        super(ProblemWithUploadedFilesTest, self).setUp()
        self.section = self.add_graded_section_to_course('section')

    def problem_setup(self, name, files):
        """
        Create a CodeResponse problem with files to upload.
        """

        xmldata = CodeResponseXMLFactory().build_xml(
            allowed_files=files, required_files=files,
        )
        ItemFactory.create(
            parent_location=self.section.location,
            category='problem',
            display_name=name,
            data=xmldata
        )

        # re-fetch the course from the database so the object is up to date
        self.refresh_course()

    def test_three_files(self):
        # Open the test files, and arrange to close them later.
        filenames = "prog1.py prog2.py prog3.py"
        fileobjs = [
            open(os.path.join(settings.COMMON_TEST_DATA_ROOT, "capa", filename))
            for filename in filenames.split()
        ]
        for fileobj in fileobjs:
            self.addCleanup(fileobj.close)

        self.problem_setup("the_problem", filenames)
        with patch('courseware.module_render.XQUEUE_INTERFACE.session') as mock_session:
            resp = self.submit_question_answer("the_problem", {'2_1': fileobjs})

        self.assertEqual(resp.status_code, 200)
        json_resp = json.loads(resp.content)
        self.assertEqual(json_resp['success'], "incorrect")

        # See how post got called.
        name, args, kwargs = mock_session.mock_calls[0]
        self.assertEqual(name, "post")
        self.assertEqual(len(args), 1)
        self.assertTrue(args[0].endswith("/submit/"))
        self.assertItemsEqual(kwargs.keys(), ["files", "data"])
        self.assertItemsEqual(kwargs['files'].keys(), filenames.split())


class TestPythonGradedResponse(TestSubmittingProblems):
    """
    Check that we can submit a schematic and custom response, and it answers properly.
    """

    SCHEMATIC_SCRIPT = dedent("""
        # for a schematic response, submission[i] is the json representation
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
        if get_value(0.0000004, output) < 2.7: okay = False;
        if get_value(0.0000009, output) < 2.7: okay = False;
        if get_value(0.0000014, output) < 2.7: okay = False;
        if get_value(0.0000019, output) < 2.7: okay = False;
        if get_value(0.0000024, output) < 2.7: okay = False;
        if get_value(0.0000029, output) > 0.25: okay = False;
        if get_value(0.0000034, output) > 0.25: okay = False;
        if get_value(0.0000039, output) > 0.25: okay = False;

        correct = ['correct' if okay else 'incorrect']""").strip()

    SCHEMATIC_CORRECT = json.dumps(
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

    SCHEMATIC_INCORRECT = json.dumps(
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

    CUSTOM_RESPONSE_SCRIPT = dedent("""
        def test_csv(expect, ans):
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

            return strip_q(expect) == strip_q(ans)""").strip()

    CUSTOM_RESPONSE_CORRECT = "0, 1, 2, 3, 4, 5, 'Outside of loop', 6"
    CUSTOM_RESPONSE_INCORRECT = "Reading my code I see.  I hope you like it :)"

    COMPUTED_ANSWER_SCRIPT = dedent("""
        if submission[0] == "a shout in the street":
            correct = ['correct']
        else:
            correct = ['incorrect']""").strip()

    COMPUTED_ANSWER_CORRECT = "a shout in the street"
    COMPUTED_ANSWER_INCORRECT = "because we never let them in"

    def setUp(self):
        super(TestPythonGradedResponse, self).setUp()
        self.section = self.add_graded_section_to_course('section')
        self.correct_responses = {}
        self.incorrect_responses = {}

    def schematic_setup(self, name):
        """
        set up an example Circuit_Schematic_Builder problem
        """

        script = self.SCHEMATIC_SCRIPT

        xmldata = SchematicResponseXMLFactory().build_xml(answer=script)
        ItemFactory.create(
            parent_location=self.section.location,
            category='problem',
            boilerplate='circuitschematic.yaml',
            display_name=name,
            data=xmldata
        )

        # define the correct and incorrect responses to this problem
        self.correct_responses[name] = self.SCHEMATIC_CORRECT
        self.incorrect_responses[name] = self.SCHEMATIC_INCORRECT

        # re-fetch the course from the database so the object is up to date
        self.refresh_course()

    def custom_response_setup(self, name):
        """
        set up an example custom response problem using a check function
        """

        test_csv = self.CUSTOM_RESPONSE_SCRIPT
        expect = self.CUSTOM_RESPONSE_CORRECT
        cfn_problem_xml = CustomResponseXMLFactory().build_xml(script=test_csv, cfn='test_csv', expect=expect)

        ItemFactory.create(
            parent_location=self.section.location,
            category='problem',
            boilerplate='customgrader.yaml',
            data=cfn_problem_xml,
            display_name=name
        )

        # define the correct and incorrect responses to this problem
        self.correct_responses[name] = expect
        self.incorrect_responses[name] = self.CUSTOM_RESPONSE_INCORRECT

        # re-fetch the course from the database so the object is up to date
        self.refresh_course()

    def computed_answer_setup(self, name):
        """
        set up an example problem using an answer script'''
        """

        script = self.COMPUTED_ANSWER_SCRIPT

        computed_xml = CustomResponseXMLFactory().build_xml(answer=script)

        ItemFactory.create(
            parent_location=self.section.location,
            category='problem',
            boilerplate='customgrader.yaml',
            data=computed_xml,
            display_name=name
        )

        # define the correct and incorrect responses to this problem
        self.correct_responses[name] = self.COMPUTED_ANSWER_CORRECT
        self.incorrect_responses[name] = self.COMPUTED_ANSWER_INCORRECT

        # re-fetch the course from the database so the object is up to date
        self.refresh_course()

    def _check_correct(self, name):
        """
        check that problem named "name" gets evaluated correctly correctly
        """
        resp = self.submit_question_answer(name, {'2_1': self.correct_responses[name]})

        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'correct')

    def _check_incorrect(self, name):
        """
        check that problem named "name" gets evaluated incorrectly correctly
        """
        resp = self.submit_question_answer(name, {'2_1': self.incorrect_responses[name]})

        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'incorrect')

    def _check_ireset(self, name):
        """
        Check that the problem can be reset
        """
        # first, get the question wrong
        resp = self.submit_question_answer(name, {'2_1': self.incorrect_responses[name]})
        # reset the question
        self.reset_question_answer(name)
        # then get it right
        resp = self.submit_question_answer(name, {'2_1': self.correct_responses[name]})

        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'correct')

    def test_schematic_correct(self):
        name = "schematic_problem"
        self.schematic_setup(name)
        self._check_correct(name)

    def test_schematic_incorrect(self):
        name = "schematic_problem"
        self.schematic_setup(name)
        self._check_incorrect(name)

    def test_schematic_reset(self):
        name = "schematic_problem"
        self.schematic_setup(name)
        self._check_ireset(name)

    def test_check_function_correct(self):
        name = 'cfn_problem'
        self.custom_response_setup(name)
        self._check_correct(name)

    def test_check_function_incorrect(self):
        name = 'cfn_problem'
        self.custom_response_setup(name)
        self._check_incorrect(name)

    def test_check_function_reset(self):
        name = 'cfn_problem'
        self.custom_response_setup(name)
        self._check_ireset(name)

    def test_computed_correct(self):
        name = 'computed_answer'
        self.computed_answer_setup(name)
        self._check_correct(name)

    def test_computed_incorrect(self):
        name = 'computed_answer'
        self.computed_answer_setup(name)
        self._check_incorrect(name)

    def test_computed_reset(self):
        name = 'computed_answer'
        self.computed_answer_setup(name)
        self._check_ireset(name)


class TestAnswerDistributions(TestSubmittingProblems):
    """Check that we can pull answer distributions for problems."""

    def setUp(self):
        """Set up a simple course with four problems."""
        super(TestAnswerDistributions, self).setUp()

        self.homework = self.add_graded_section_to_course('homework')
        self.add_dropdown_to_section(self.homework.location, 'p1', 1)
        self.add_dropdown_to_section(self.homework.location, 'p2', 1)
        self.add_dropdown_to_section(self.homework.location, 'p3', 1)
        self.refresh_course()

    def test_empty(self):
        # Just make sure we can process this without errors.
        empty_distribution = grades.answer_distributions(self.course.id)
        self.assertFalse(empty_distribution)  # should be empty

    def test_one_student(self):
        # Basic test to make sure we have simple behavior right for a student

        # Throw in a non-ASCII answer
        self.submit_question_answer('p1', {'2_1': u'ⓤⓝⓘⓒⓞⓓⓔ'})
        self.submit_question_answer('p2', {'2_1': 'Correct'})

        distributions = grades.answer_distributions(self.course.id)
        self.assertEqual(
            distributions,
            {
                ('p1', 'p1', 'i4x-MITx-100-problem-p1_2_1'): {
                    u'ⓤⓝⓘⓒⓞⓓⓔ': 1
                },
                ('p2', 'p2', 'i4x-MITx-100-problem-p2_2_1'): {
                    'Correct': 1
                }
            }
        )

    def test_multiple_students(self):
        # Our test class is based around making requests for a particular user,
        # so we're going to cheat by creating another user and copying and
        # modifying StudentModule entries to make them from other users. It's
        # a little hacky, but it seemed the simpler way to do this.
        self.submit_question_answer('p1', {'2_1': u'Correct'})
        self.submit_question_answer('p2', {'2_1': u'Incorrect'})
        self.submit_question_answer('p3', {'2_1': u'Correct'})

        # Make the above submissions owned by user2
        user2 = UserFactory.create()
        problems = StudentModule.objects.filter(
            course_id=self.course.id,
            student=self.student_user
        )
        for problem in problems:
            problem.student_id = user2.id
            problem.save()

        # Now make more submissions by our original user
        self.submit_question_answer('p1', {'2_1': u'Correct'})
        self.submit_question_answer('p2', {'2_1': u'Correct'})

        self.assertEqual(
            grades.answer_distributions(self.course.id),
            {
                ('p1', 'p1', 'i4x-MITx-100-problem-p1_2_1'): {
                    'Correct': 2
                },
                ('p2', 'p2', 'i4x-MITx-100-problem-p2_2_1'): {
                    'Correct': 1,
                    'Incorrect': 1
                },
                ('p3', 'p3', 'i4x-MITx-100-problem-p3_2_1'): {
                    'Correct': 1
                }
            }
        )

    def test_other_data_types(self):
        # We'll submit one problem, and then muck with the student_answers
        # dict inside its state to try different data types (str, int, float,
        # none)
        self.submit_question_answer('p1', {'2_1': u'Correct'})

        # Now fetch the state entry for that problem.
        student_module = StudentModule.objects.get(
            course_id=self.course.id,
            student=self.student_user
        )
        for val in ('Correct', True, False, 0, 0.0, 1, 1.0, None):
            state = json.loads(student_module.state)
            state["student_answers"]['i4x-MITx-100-problem-p1_2_1'] = val
            student_module.state = json.dumps(state)
            student_module.save()

            self.assertEqual(
                grades.answer_distributions(self.course.id),
                {
                    ('p1', 'p1', 'i4x-MITx-100-problem-p1_2_1'): {
                        str(val): 1
                    },
                }
            )

    def test_missing_content(self):
        # If there's a StudentModule entry for content that no longer exists,
        # we just quietly ignore it (because we can't display a meaningful url
        # or name for it).
        self.submit_question_answer('p1', {'2_1': 'Incorrect'})

        # Now fetch the state entry for that problem and alter it so it points
        # to a non-existent problem.
        student_module = StudentModule.objects.get(
            course_id=self.course.id,
            student=self.student_user
        )
        student_module.module_state_key = student_module.module_state_key.replace(
            name=student_module.module_state_key.name + "_fake"
        )
        student_module.save()

        # It should be empty (ignored)
        empty_distribution = grades.answer_distributions(self.course.id)
        self.assertFalse(empty_distribution)  # should be empty

    def test_broken_state(self):
        # Missing or broken state for a problem should be skipped without
        # causing the whole answer_distribution call to explode.

        # Submit p1
        self.submit_question_answer('p1', {'2_1': u'Correct'})

        # Now fetch the StudentModule entry for p1 so we can corrupt its state
        prb1 = StudentModule.objects.get(
            course_id=self.course.id,
            student=self.student_user
        )

        # Submit p2
        self.submit_question_answer('p2', {'2_1': u'Incorrect'})

        for new_p1_state in ('{"student_answers": {}}', "invalid json!", None):
            prb1.state = new_p1_state
            prb1.save()

            # p1 won't show up, but p2 should still work
            self.assertEqual(
                grades.answer_distributions(self.course.id),
                {
                    ('p2', 'p2', 'i4x-MITx-100-problem-p2_2_1'): {
                        'Incorrect': 1
                    },
                }
            )
