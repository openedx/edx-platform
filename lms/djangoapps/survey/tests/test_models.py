"""
Python tests for the Survey models
"""


from collections import OrderedDict

import ddt
import six
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test.client import Client

from lms.djangoapps.survey.exceptions import SurveyFormNameAlreadyExists, SurveyFormNotFound
from lms.djangoapps.survey.models import SurveyAnswer, SurveyForm


@ddt.ddt
class SurveyModelsTests(TestCase):
    """
    All tests for the Survey models.py file
    """

    def setUp(self):
        """
        Set up the test data used in the specific tests
        """
        super(SurveyModelsTests, self).setUp()
        self.client = Client()

        # Create two accounts
        self.password = 'abc'
        self.student = User.objects.create_user('student', 'student@test.com', self.password)
        self.student2 = User.objects.create_user('student2', 'student2@test.com', self.password)

        self.test_survey_name = 'TestForm'
        self.test_form = '<li><input name="field1" /></li><li><input name="field2" /></li><li><select name="ddl"><option>1</option></select></li>'
        self.test_form_update = '<input name="field1" />'
        self.course_id = 'foo/bar/baz'

        self.student_answers = OrderedDict({
            'field1': 'value1',
            'field2': 'value2',
        })

        self.student_answers_update = OrderedDict({
            'field1': 'value1-updated',
            'field2': 'value2-updated',
        })

        self.student_answers_update2 = OrderedDict({
            'field1': 'value1-updated2',
        })

        self.student2_answers = OrderedDict({
            'field1': 'value3'
        })

    def _create_test_survey(self):
        """
        Helper method to set up test form
        """
        return SurveyForm.create(self.test_survey_name, self.test_form)

    def test_form_not_found_raise_exception(self):
        """
        Asserts that when looking up a form that does not exist
        """

        with self.assertRaises(SurveyFormNotFound):
            SurveyForm.get(self.test_survey_name)

    def test_form_not_found_none(self):
        """
        Asserts that when looking up a form that does not exist
        """

        self.assertIsNone(SurveyForm.get(self.test_survey_name, throw_if_not_found=False))

    def test_create_new_form(self):
        """
        Make sure we can create a new form a look it up
        """

        survey = self._create_test_survey()
        self.assertIsNotNone(survey)

        new_survey = SurveyForm.get(self.test_survey_name)
        self.assertIsNotNone(new_survey)
        self.assertEqual(new_survey.form, self.test_form)

    def test_unicode_rendering(self):
        """
        See if the survey form returns the expected unicode string
        """
        survey = self._create_test_survey()
        self.assertIsNotNone(survey)
        self.assertEqual(six.text_type(survey), self.test_survey_name)

    def test_create_form_with_malformed_html(self):
        """
        Make sure that if a SurveyForm is saved with unparseable html
        an exception is thrown
        """
        with self.assertRaises(ValidationError):
            SurveyForm.create('badform', '<input name="oops" /><<<>')

    def test_create_form_with_no_fields(self):
        """
        Make sure that if a SurveyForm is saved without any named fields
        an exception is thrown
        """
        with self.assertRaises(ValidationError):
            SurveyForm.create('badform', '<p>no input fields here</p>')

        with self.assertRaises(ValidationError):
            SurveyForm.create('badform', '<input id="input_without_name" />')

    def test_create_form_already_exists(self):
        """
        Make sure we can't create two surveys of the same name
        """

        self._create_test_survey()
        with self.assertRaises(SurveyFormNameAlreadyExists):
            self._create_test_survey()

    def test_create_form_update_existing(self):
        """
        Make sure we can update an existing form
        """
        survey = self._create_test_survey()
        self.assertIsNotNone(survey)

        survey = SurveyForm.create(self.test_survey_name, self.test_form_update, update_if_exists=True)
        self.assertIsNotNone(survey)

        survey = SurveyForm.get(self.test_survey_name)
        self.assertIsNotNone(survey)
        self.assertEqual(survey.form, self.test_form_update)

    def test_survey_has_no_answers(self):
        """
        Create a new survey and assert that there are no answers to that survey
        """

        survey = self._create_test_survey()
        self.assertEqual(len(survey.get_answers()), 0)

    def test_user_has_no_answers(self):
        """
        Create a new survey with no answers in it and check that a user is determined to not have answered it
        """

        survey = self._create_test_survey()
        self.assertFalse(survey.has_user_answered_survey(self.student))
        self.assertEqual(len(survey.get_answers()), 0)

    @ddt.data(None, 'foo/bar/baz')
    def test_single_user_answers(self, course_id):
        """
        Create a new survey and add answers to it
        """

        survey = self._create_test_survey()
        self.assertIsNotNone(survey)

        survey.save_user_answers(self.student, self.student_answers, course_id)

        self.assertTrue(survey.has_user_answered_survey(self.student))

        all_answers = survey.get_answers()
        self.assertEqual(len(list(all_answers.keys())), 1)
        self.assertIn(self.student.id, all_answers)
        self.assertEqual(all_answers[self.student.id], self.student_answers)

        answers = survey.get_answers(self.student)
        self.assertEqual(len(list(answers.keys())), 1)
        self.assertIn(self.student.id, answers)
        self.assertEqual(all_answers[self.student.id], self.student_answers)

        # check that the course_id was set

        answer_objs = SurveyAnswer.objects.filter(
            user=self.student,
            form=survey
        )

        for answer_obj in answer_objs:
            if course_id:
                self.assertEqual(six.text_type(answer_obj.course_key), course_id)
            else:
                self.assertIsNone(answer_obj.course_key)

    def test_multiple_user_answers(self):
        """
        Create a new survey and add answers to it
        """

        survey = self._create_test_survey()
        self.assertIsNotNone(survey)

        survey.save_user_answers(self.student, self.student_answers, self.course_id)
        survey.save_user_answers(self.student2, self.student2_answers, self.course_id)

        self.assertTrue(survey.has_user_answered_survey(self.student))

        all_answers = survey.get_answers()
        self.assertEqual(len(list(all_answers.keys())), 2)
        self.assertIn(self.student.id, all_answers)
        self.assertIn(self.student2.id, all_answers)
        self.assertEqual(all_answers[self.student.id], self.student_answers)
        self.assertEqual(all_answers[self.student2.id], self.student2_answers)

        answers = survey.get_answers(self.student)
        self.assertEqual(len(list(answers.keys())), 1)
        self.assertIn(self.student.id, answers)
        self.assertEqual(answers[self.student.id], self.student_answers)

        answers = survey.get_answers(self.student2)
        self.assertEqual(len(list(answers.keys())), 1)
        self.assertIn(self.student2.id, answers)
        self.assertEqual(answers[self.student2.id], self.student2_answers)

    def test_update_answers(self):
        """
        Make sure the update case works
        """

        survey = self._create_test_survey()
        self.assertIsNotNone(survey)

        survey.save_user_answers(self.student, self.student_answers, self.course_id)

        answers = survey.get_answers(self.student)
        self.assertEqual(len(list(answers.keys())), 1)
        self.assertIn(self.student.id, answers)
        self.assertEqual(answers[self.student.id], self.student_answers)

        # update
        survey.save_user_answers(self.student, self.student_answers_update, self.course_id)

        answers = survey.get_answers(self.student)
        self.assertEqual(len(list(answers.keys())), 1)
        self.assertIn(self.student.id, answers)
        self.assertEqual(answers[self.student.id], self.student_answers_update)

        # update with just a subset of the origin dataset
        survey.save_user_answers(self.student, self.student_answers_update2, self.course_id)

        answers = survey.get_answers(self.student)
        self.assertEqual(len(list(answers.keys())), 1)
        self.assertIn(self.student.id, answers)
        self.assertEqual(answers[self.student.id], self.student_answers_update2)

    def test_limit_num_users(self):
        """
        Verify that the limit_num_users parameter to get_answers()
        works as intended
        """
        survey = self._create_test_survey()

        survey.save_user_answers(self.student, self.student_answers, self.course_id)
        survey.save_user_answers(self.student2, self.student2_answers, self.course_id)

        # even though we have 2 users submitted answers
        # limit the result set to just 1
        all_answers = survey.get_answers(limit_num_users=1)
        self.assertEqual(len(list(all_answers.keys())), 1)

    def test_get_field_names(self):
        """
        Create a new survey and add answers to it
        """

        survey = self._create_test_survey()
        self.assertIsNotNone(survey)

        survey.save_user_answers(self.student, self.student_answers, self.course_id)
        survey.save_user_answers(self.student2, self.student2_answers, self.course_id)

        names = survey.get_field_names()

        self.assertEqual(sorted(names), ['ddl', 'field1', 'field2'])

    def test_retire_user_successful(self):
        survey = self._create_test_survey()
        self.assertIsNotNone(survey)

        survey.save_user_answers(self.student, self.student_answers, self.course_id)
        survey.save_user_answers(self.student2, self.student2_answers, self.course_id)

        retire_result = SurveyAnswer.retire_user(self.student.id)
        self.assertTrue(retire_result)
        answers = survey.get_answers(self.student)
        blanked_out_student_answser = {key: '' for key in self.student_answers}
        self.assertEqual(answers[self.student.id], blanked_out_student_answser)
        self.assertEqual(survey.get_answers(self.student2)[self.student2.id], self.student2_answers)

    def test_retire_user_not_exist(self):
        survey = self._create_test_survey()
        self.assertIsNotNone(survey)

        survey.save_user_answers(self.student, self.student_answers, self.course_id)

        retire_result = SurveyAnswer.retire_user(self.student2.id)
        self.assertFalse(retire_result)
        answers = survey.get_answers(self.student)
        self.assertEqual(answers[self.student.id], self.student_answers)
