"""
Python tests for the Survey models
"""

from collections import OrderedDict

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User

from survey.exceptions import SurveyFormNotFound, SurveyFormNameAlreadyExists
from survey.models import SurveyForm


class SurveyModelsTests(TestCase):

    def setUp(self):
        """
        Set up the test data used in the specific tests
        """
        self.client = Client()

        # Create two accounts
        self.password = 'abc'
        self.student = User.objects.create_user('student', 'student@test.com', self.password)
        self.student2 = User.objects.create_user('student2', 'student2@test.com', self.password)

        self.test_survey_name = 'TestForm'
        self.test_form = '<input></input>'
        self.test_form_update = '<input>updated</input>'

        self.student_answers = OrderedDict({
            'field1': 'value1',
            'field2': 'value2',
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
        self.assertEquals(unicode(survey), self.test_survey_name)

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
        self.assertEquals(survey.form, self.test_form_update)

    def test_survey_has_no_answers(self):
        """
        Create a new survey and assert that there are no answers to that survey
        """

        survey = self._create_test_survey()
        self.assertEquals(len(survey.get_answers()), 0)

    def test_user_has_no_answers(self):
        """
        Create a new survey with no answers in it and check that a user is determined to not have answered it
        """

        survey = self._create_test_survey()
        self.assertFalse(survey.has_user_answered_survey(self.student))

    def test_single_user_answers(self):
        """
        Create a new survey and add answers to it
        """

        survey = self._create_test_survey()
        self.assertIsNotNone(survey)

        survey.save_user_answers(self.student, self.student_answers)

        self.assertTrue(survey.has_user_answered_survey(self.student))

        all_answers = survey.get_answers()
        self.assertEquals(len(all_answers.keys()), 1)
        self.assertTrue(self.student.id in all_answers)
        self.assertEquals(all_answers[self.student.id], self.student_answers)

        answers = survey.get_answers(self.student)
        self.assertEquals(len(answers.keys()), 1)
        self.assertTrue(self.student.id in answers)
        self.assertEquals(all_answers[self.student.id], self.student_answers)

    def test_multiple_user_answers(self):
        """
        Create a new survey and add answers to it
        """

        survey = self._create_test_survey()
        self.assertIsNotNone(survey)

        survey.save_user_answers(self.student, self.student_answers)
        survey.save_user_answers(self.student2, self.student2_answers)

        self.assertTrue(survey.has_user_answered_survey(self.student))

        all_answers = survey.get_answers()
        self.assertEquals(len(all_answers.keys()), 2)
        self.assertTrue(self.student.id in all_answers)
        self.assertTrue(self.student2.id in all_answers)
        self.assertEquals(all_answers[self.student.id], self.student_answers)
        self.assertEquals(all_answers[self.student2.id], self.student2_answers)

        answers = survey.get_answers(self.student)
        self.assertEquals(len(answers.keys()), 1)
        self.assertTrue(self.student.id in answers)
        self.assertEquals(all_answers[self.student.id], self.student_answers)

        answers = survey.get_answers(self.student2)
        self.assertEquals(len(answers.keys()), 1)
        self.assertTrue(self.student2.id in answers)
        self.assertEquals(all_answers[self.student2.id], self.student2_answers)
