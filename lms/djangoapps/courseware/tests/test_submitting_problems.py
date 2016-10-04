# -*- coding: utf-8 -*-
"""
Integration tests for submitting problem responses and getting grades.
"""
import ddt
import json
import os
from textwrap import dedent

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory
from mock import patch
from nose.plugins.attrib import attr

from capa.tests.response_xml_factory import (
    OptionResponseXMLFactory, CustomResponseXMLFactory, SchematicResponseXMLFactory,
    CodeResponseXMLFactory,
)
from lms.djangoapps.grades import course_grades, progress
from course_modes.models import CourseMode
from courseware.models import StudentModule, BaseStudentModuleHistory
from courseware.tests.helpers import LoginEnrollmentTestCase
from lms.djangoapps.lms_xblock.runtime import quote_slashes
from student.models import anonymous_id_for_user, CourseEnrollment
from submissions import api as submissions_api
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.partitions.partitions import Group, UserPartition
from openedx.core.djangoapps.credit.api import (
    set_credit_requirements, get_credit_requirement_status
)
from openedx.core.djangoapps.credit.models import CreditCourse, CreditProvider
from openedx.core.djangoapps.user_api.tests.factories import UserCourseTagFactory


class ProblemSubmissionTestMixin(TestCase):
    """
    TestCase mixin that provides functions to submit answers to problems.
    """
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

        answer_key_prefix = 'input_{}_'.format(problem_location.html_id())

        # format the response dictionary to be sent in the post request by adding the above prefix to each key
        response_dict = {(answer_key_prefix + k): v for k, v in responses.items()}
        resp = self.client.post(modx_url, response_dict)

        return resp

    def look_at_question(self, problem_url_name):
        """
        Create state for a problem, but don't answer it
        """
        location = self.problem_location(problem_url_name)
        modx_url = self.modx_url(location, "problem_get")
        resp = self.client.get(modx_url)
        return resp

    def reset_question_answer(self, problem_url_name):
        """
        Reset specified problem for current user.
        """
        problem_location = self.problem_location(problem_url_name)
        modx_url = self.modx_url(problem_location, 'problem_reset')
        resp = self.client.post(modx_url)
        return resp

    def rescore_question(self, problem_url_name):
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


class TestSubmittingProblems(ModuleStoreTestCase, LoginEnrollmentTestCase, ProblemSubmissionTestMixin):
    """
    Check that a course gets graded properly.
    """

    # Tell Django to clean out all databases, not just default
    multi_db = True
    # arbitrary constant
    COURSE_SLUG = "100"
    COURSE_NAME = "test_course"

    ENABLED_CACHES = ['default', 'mongo_metadata_inheritance', 'loc_cache']

    def setUp(self):
        super(TestSubmittingProblems, self).setUp()

        # create a test student
        self.course = CourseFactory.create(display_name=self.COURSE_NAME, number=self.COURSE_SLUG)
        self.student = 'view@test.com'
        self.password = 'foo'
        self.create_account('u1', self.student, self.password)
        self.activate_user(self.student)
        self.enroll(self.course)
        self.student_user = User.objects.get(email=self.student)
        self.factory = RequestFactory()
        # Disable the score change signal to prevent other components from being pulled into tests.
        self.score_changed_signal_patch = patch('courseware.module_render.SCORE_CHANGED.send')
        self.score_changed_signal_patch.start()

    def tearDown(self):
        super(TestSubmittingProblems, self).tearDown()
        self._stop_signal_patch()

    def _stop_signal_patch(self):
        """
        Stops the signal patch for the SCORE_CHANGED event.
        In case a test wants to test with the event actually
        firing.
        """
        if self.score_changed_signal_patch:
            self.score_changed_signal_patch.stop()
            self.score_changed_signal_patch = None

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
        if not hasattr(self, 'chapter'):
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

    def add_grading_policy(self, grading_policy):
        """
        Add a grading policy to the course.
        """

        self.course.grading_policy = grading_policy
        self.update_course(self.course, self.student_user.id)
        self.refresh_course()

    def get_grade_summary(self):
        """
        calls course_grades.summary for current user and course.

        the keywords for the returned object are
        - grade : A final letter grade.
        - percent : The final percent for the class (rounded up).
        - section_breakdown : A breakdown of each section that makes
            up the grade. (For display)
        - grade_breakdown : A breakdown of the major components that
            make up the final grade. (For display)
        """
        return course_grades.summary(self.student_user, self.course)

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
        return progress.summary(self.student_user, self.course).chapter_grades

    def check_grade_percent(self, percent):
        """
        Assert that percent grade is as expected.
        """
        grade_summary = self.get_grade_summary()
        self.assertEqual(grade_summary['percent'], percent)

    def earned_hw_scores(self):
        """
        Global scores, each Score is a Problem Set.

        Returns list of scores: [<points on hw_1>, <points on hw_2>, ..., <points on hw_n>]
        """
        return [s.earned for s in self.get_grade_summary()['totaled_scores']['Homework']]

    def hw_grade(self, hw_url_name):
        """
        Returns SubsectionGrade for given url.
        """
        # list of grade summaries for each section
        sections_list = []
        for chapter in self.get_progress_summary():
            sections_list.extend(chapter['sections'])

        # get the first section that matches the url (there should only be one)
        return next(section for section in sections_list if section.url_name == hw_url_name)

    def score_for_hw(self, hw_url_name):
        """
        Returns list of scores for a given url.

        Returns list of scores for the given homework:
            [<points on problem_1>, <points on problem_2>, ..., <points on problem_n>]
        """
        return [s.earned for s in self.hw_grade(hw_url_name).scores]


class TestCourseGrades(TestSubmittingProblems):
    """
    Tests grades are updated correctly when manipulating problems.
    """
    def setUp(self):
        super(TestCourseGrades, self).setUp()
        self.homework = self.add_graded_section_to_course('homework')
        self.problem = self.add_dropdown_to_section(self.homework.location, 'p1', 1)

    def _submit_correct_answer(self):
        """
        Submits correct answer to the problem.
        """
        resp = self.submit_question_answer('p1', {'2_1': 'Correct'})
        self.assertEqual(resp.status_code, 200)

    def _verify_grade(self, expected_problem_score, expected_hw_grade):
        """
        Verifies the problem score and the homework grade are as expected.
        """
        hw_grade = self.hw_grade('homework')
        problem_score = hw_grade.scores[0]
        self.assertEquals((problem_score.earned, problem_score.possible), expected_problem_score)
        self.assertEquals((hw_grade.graded_total.earned, hw_grade.graded_total.possible), expected_hw_grade)

    def test_basic(self):
        self._submit_correct_answer()
        self._verify_grade(expected_problem_score=(1.0, 1.0), expected_hw_grade=(1.0, 1.0))

    def test_problem_reset(self):
        self._submit_correct_answer()
        self.reset_question_answer('p1')
        self._verify_grade(expected_problem_score=(0.0, 1.0), expected_hw_grade=(0.0, 1.0))


@attr(shard=3)
@ddt.ddt
class TestCourseGrader(TestSubmittingProblems):
    """
    Suite of tests for the course grader.
    """
    # Tell Django to clean out all databases, not just default
    multi_db = True

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

    def weighted_setup(self, hw_weight=0.25, final_weight=0.75):
        """
        Set up a simple course for testing weighted grading functionality.
        """
        # pylint: disable=attribute-defined-outside-init

        self.set_weighted_policy(hw_weight, final_weight)

        # set up a structure of 1 homework and 1 final
        self.homework = self.add_graded_section_to_course('homework')
        self.problem = self.add_dropdown_to_section(self.homework.location, 'H1P1')
        self.final = self.add_graded_section_to_course('Final Section', 'Final')
        self.final_question = self.add_dropdown_to_section(self.final.location, 'FinalQuestion')

    def set_weighted_policy(self, hw_weight=0.25, final_weight=0.75):
        """
        Set up a simple course for testing weighted grading functionality.
        """

        grading_policy = {
            "GRADER": [
                {
                    "type": "Homework",
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "HW",
                    "weight": hw_weight
                }, {
                    "type": "Final",
                    "name": "Final Section",
                    "short_label": "Final",
                    "weight": final_weight
                }
            ]
        }
        self.add_grading_policy(grading_policy)

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
                }
            ]
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

    def test_show_answer_doesnt_write_to_csm(self):
        self.basic_setup()
        self.submit_question_answer('p1', {'2_1': u'Correct'})

        # Now fetch the state entry for that problem.
        student_module = StudentModule.objects.filter(
            course_id=self.course.id,
            student=self.student_user
        )
        # count how many state history entries there are
        baseline = BaseStudentModuleHistory.get_history(student_module)
        self.assertEqual(len(baseline), 3)

        # now click "show answer"
        self.show_question_answer('p1')

        # check that we don't have more state history entries
        csmh = BaseStudentModuleHistory.get_history(student_module)
        self.assertEqual(len(csmh), 3)

    def test_grade_with_collected_max_score(self):
        """
        Tests that the results of grading runs before and after the cache
        warms are the same.
        """
        self.basic_setup()
        self.submit_question_answer('p1', {'2_1': 'Correct'})
        self.look_at_question('p2')
        self.assertTrue(
            StudentModule.objects.filter(
                module_state_key=self.problem_location('p2')
            ).exists()
        )

        # problem isn't in the cache, but will be when graded
        self.check_grade_percent(0.33)

        # problem is in the cache, should be the same result
        self.check_grade_percent(0.33)

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

        # But now, set the score with the submissions API and watch
        # as it overrides the score read from StudentModule and our
        # student gets an A instead.
        self._stop_signal_patch()
        student_item = {
            'student_id': anonymous_id_for_user(self.student_user, self.course.id),
            'course_id': unicode(self.course.id),
            'item_id': unicode(self.problem_location('p3')),
            'item_type': 'problem'
        }
        submission = submissions_api.create_submission(student_item, 'any answer')
        submissions_api.set_score(submission['uuid'], 1, 1)
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
                self.course.id.to_deprecated_string(),
                anonymous_id_for_user(self.student_user, self.course.id)
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

    def test_grade_updates_on_weighted_change(self):
        """
        Test that the course grade updates when the
        assignment weights change.
        """
        self.weighted_setup()
        self.submit_question_answer('H1P1', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(0.25)
        self.set_weighted_policy(0.75, 0.25)
        self.check_grade_percent(0.75)

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

    @ddt.data(
        *CourseMode.CREDIT_ELIGIBLE_MODES
    )
    def test_min_grade_credit_requirements_status(self, mode):
        """
        Test for credit course. If user passes minimum grade requirement then
        status will be updated as satisfied in requirement status table.
        """
        self.basic_setup()

        # Enroll student in credit eligible mode.
        # Note that we can't call self.enroll here since that goes through
        # the Django student views, and does not update enrollment if it already exists.
        CourseEnrollment.enroll(self.student_user, self.course.id, mode)

        self.submit_question_answer('p1', {'2_1': 'Correct'})
        self.submit_question_answer('p2', {'2_1': 'Correct'})

        # Enable the course for credit
        CreditCourse.objects.create(course_key=self.course.id, enabled=True)

        # Configure a credit provider for the course
        CreditProvider.objects.create(
            provider_id="ASU",
            enable_integration=True,
            provider_url="https://credit.example.com/request",
        )

        requirements = [{
            "namespace": "grade",
            "name": "grade",
            "display_name": "Grade",
            "criteria": {"min_grade": 0.52},
        }]
        # Add a single credit requirement (final grade)
        set_credit_requirements(self.course.id, requirements)

        self.get_grade_summary()
        req_status = get_credit_requirement_status(self.course.id, self.student_user.username, 'grade', 'grade')
        self.assertEqual(req_status[0]["status"], 'satisfied')


@attr(shard=1)
class ProblemWithUploadedFilesTest(TestSubmittingProblems):
    """Tests of problems with uploaded files."""
    # Tell Django to clean out all databases, not just default
    multi_db = True

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


@attr(shard=1)
class TestPythonGradedResponse(TestSubmittingProblems):
    """
    Check that we can submit a schematic and custom response, and it answers properly.
    """
    # Tell Django to clean out all databases, not just default
    multi_db = True

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


@attr(shard=1)
class TestConditionalContent(TestSubmittingProblems):
    """
    Check that conditional content works correctly with grading.
    """
    def setUp(self):
        """
        Set up a simple course with a grading policy, a UserPartition, and 2 sections, both graded as "homework".
        One section is pre-populated with a problem (with 2 inputs), visible to all students.
        The second section is empty. Test cases should add conditional content to it.
        """
        super(TestConditionalContent, self).setUp()

        self.user_partition_group_0 = 0
        self.user_partition_group_1 = 1
        self.partition = UserPartition(
            0,
            'first_partition',
            'First Partition',
            [
                Group(self.user_partition_group_0, 'alpha'),
                Group(self.user_partition_group_1, 'beta')
            ]
        )

        self.course = CourseFactory.create(
            display_name=self.COURSE_NAME,
            number=self.COURSE_SLUG,
            user_partitions=[self.partition]
        )

        grading_policy = {
            "GRADER": [{
                "type": "Homework",
                "min_count": 2,
                "drop_count": 0,
                "short_label": "HW",
                "weight": 1.0
            }]
        }
        self.add_grading_policy(grading_policy)

        self.homework_all = self.add_graded_section_to_course('homework1')
        self.p1_all_html_id = self.add_dropdown_to_section(self.homework_all.location, 'H1P1', 2).location.html_id()

        self.homework_conditional = self.add_graded_section_to_course('homework2')

    def split_setup(self, user_partition_group):
        """
        Setup for tests using split_test module. Creates a split_test instance as a child of self.homework_conditional
        with 2 verticals in it, and assigns self.student_user to the specified user_partition_group.

        The verticals are returned.
        """
        vertical_0_url = self.course.id.make_usage_key("vertical", "split_test_vertical_0")
        vertical_1_url = self.course.id.make_usage_key("vertical", "split_test_vertical_1")

        group_id_to_child = {}
        for index, url in enumerate([vertical_0_url, vertical_1_url]):
            group_id_to_child[str(index)] = url

        split_test = ItemFactory.create(
            parent_location=self.homework_conditional.location,
            category="split_test",
            display_name="Split test",
            user_partition_id='0',
            group_id_to_child=group_id_to_child,
        )

        vertical_0 = ItemFactory.create(
            parent_location=split_test.location,
            category="vertical",
            display_name="Condition 0 vertical",
            location=vertical_0_url,
        )

        vertical_1 = ItemFactory.create(
            parent_location=split_test.location,
            category="vertical",
            display_name="Condition 1 vertical",
            location=vertical_1_url,
        )

        # Now add the student to the specified group.
        UserCourseTagFactory(
            user=self.student_user,
            course_id=self.course.id,
            key='xblock.partition_service.partition_{0}'.format(self.partition.id),
            value=str(user_partition_group)
        )

        return vertical_0, vertical_1

    def split_different_problems_setup(self, user_partition_group):
        """
        Setup for the case where the split test instance contains problems for each group
        (so both groups do have graded content, though it is different).

        Group 0 has 2 problems, worth 1 and 3 points respectively.
        Group 1 has 1 problem, worth 1 point.

        This method also assigns self.student_user to the specified user_partition_group and
        then submits answers for the problems in section 1, which are visible to all students.
        The submitted answers give the student 1 point out of a possible 2 points in the section.
        """
        vertical_0, vertical_1 = self.split_setup(user_partition_group)

        # Group 0 will have 2 problems in the section, worth a total of 4 points.
        self.add_dropdown_to_section(vertical_0.location, 'H2P1_GROUP0', 1).location.html_id()
        self.add_dropdown_to_section(vertical_0.location, 'H2P2_GROUP0', 3).location.html_id()

        # Group 1 will have 1 problem in the section, worth a total of 1 point.
        self.add_dropdown_to_section(vertical_1.location, 'H2P1_GROUP1', 1).location.html_id()

        # Submit answers for problem in Section 1, which is visible to all students.
        self.submit_question_answer('H1P1', {'2_1': 'Correct', '2_2': 'Incorrect'})

    def test_split_different_problems_group_0(self):
        """
        Tests that users who see different problems in a split_test module instance are graded correctly.
        This is the test case for a user in user partition group 0.
        """
        self.split_different_problems_setup(self.user_partition_group_0)

        self.submit_question_answer('H2P1_GROUP0', {'2_1': 'Correct'})
        self.submit_question_answer('H2P2_GROUP0', {'2_1': 'Correct', '2_2': 'Incorrect', '2_3': 'Correct'})

        self.assertEqual(self.score_for_hw('homework1'), [1.0])
        self.assertEqual(self.score_for_hw('homework2'), [1.0, 2.0])
        self.assertEqual(self.earned_hw_scores(), [1.0, 3.0])

        # Grade percent is .63. Here is the calculation
        homework_1_score = 1.0 / 2
        homework_2_score = (1.0 + 2.0) / 4
        self.check_grade_percent(round((homework_1_score + homework_2_score) / 2, 2))

    def test_split_different_problems_group_1(self):
        """
        Tests that users who see different problems in a split_test module instance are graded correctly.
        This is the test case for a user in user partition group 1.
        """
        self.split_different_problems_setup(self.user_partition_group_1)

        self.submit_question_answer('H2P1_GROUP1', {'2_1': 'Correct'})

        self.assertEqual(self.score_for_hw('homework1'), [1.0])
        self.assertEqual(self.score_for_hw('homework2'), [1.0])
        self.assertEqual(self.earned_hw_scores(), [1.0, 1.0])

        # Grade percent is .75. Here is the calculation
        homework_1_score = 1.0 / 2
        homework_2_score = 1.0 / 1
        self.check_grade_percent(round((homework_1_score + homework_2_score) / 2, 2))

    def split_one_group_no_problems_setup(self, user_partition_group):
        """
        Setup for the case where the split test instance contains problems on for one group.

        Group 0 has no problems.
        Group 1 has 1 problem, worth 1 point.

        This method also assigns self.student_user to the specified user_partition_group and
        then submits answers for the problems in section 1, which are visible to all students.
        The submitted answers give the student 2 points out of a possible 2 points in the section.
        """
        [_, vertical_1] = self.split_setup(user_partition_group)

        # Group 1 will have 1 problem in the section, worth a total of 1 point.
        self.add_dropdown_to_section(vertical_1.location, 'H2P1_GROUP1', 1).location.html_id()

        self.submit_question_answer('H1P1', {'2_1': 'Correct'})

    def test_split_one_group_no_problems_group_0(self):
        """
        Tests what happens when a given group has no problems in it (students receive 0 for that section).
        """
        self.split_one_group_no_problems_setup(self.user_partition_group_0)

        self.assertEqual(self.score_for_hw('homework1'), [1.0])
        self.assertEqual(self.score_for_hw('homework2'), [])
        self.assertEqual(self.earned_hw_scores(), [1.0])

        # Grade percent is .25. Here is the calculation.
        homework_1_score = 1.0 / 2
        homework_2_score = 0.0
        self.check_grade_percent(round((homework_1_score + homework_2_score) / 2, 2))

    def test_split_one_group_no_problems_group_1(self):
        """
        Verifies students in the group that DOES have a problem receive a score for their problem.
        """
        self.split_one_group_no_problems_setup(self.user_partition_group_1)

        self.submit_question_answer('H2P1_GROUP1', {'2_1': 'Correct'})

        self.assertEqual(self.score_for_hw('homework1'), [1.0])
        self.assertEqual(self.score_for_hw('homework2'), [1.0])
        self.assertEqual(self.earned_hw_scores(), [1.0, 1.0])

        # Grade percent is .75. Here is the calculation.
        homework_1_score = 1.0 / 2
        homework_2_score = 1.0 / 1
        self.check_grade_percent(round((homework_1_score + homework_2_score) / 2, 2))
