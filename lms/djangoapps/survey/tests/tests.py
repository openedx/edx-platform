"""
Test the lms/survey views.
"""

import json
import logging

from django.http import HttpResponseNotAllowed, Http404
from django.test import TestCase
from django.test.client import RequestFactory

from student.tests.factories import UserFactory
from survey.models import SurveySubmission
from survey.tests.factories import SurveySubmissionFactory
from survey.views import survey_init, survey_ajax


log = logging.getLogger(__name__)


class SuveyTests(TestCase):
    """
    Tests for survey functionality
    """
    request_factory = RequestFactory()

    def setUp(self):
        self.user = UserFactory.create()
        self.course_id = 'edX/test/course1'
        self.unit_id = '22222222222222222222222222222222'
        self.survey_name = 'survey #2'
        self.survey_answer = '{"Q1": "1", "Q2": ["2", "3"], "Q3": "test"}'

    def test_survey_init_get_method_not_allowed(self):
        """Ensures that get request to /survey_init/ is not allowed"""
        req = self.request_factory.get('/survey_init/')
        resp = survey_init(req)
        self.assertIsInstance(resp, HttpResponseNotAllowed)

    def test_survey_init_with_empty_course_id(self):
        """Ensures that request with empty course_id raises Http404"""
        data = {
            'unit_id': self.unit_id,
        }
        req = self.request_factory.post('/survey_init/', data)
        req.user = self.user
        self.assertRaises(Http404, survey_init, req)

    def test_survey_init_with_empty_unit_id(self):
        """Ensures that request with empty unit_id raises Http404"""
        data = {
            'course_id': self.course_id,
        }
        req = self.request_factory.post('/survey_init/', data)
        req.user = self.user
        self.assertRaises(Http404, survey_init, req)

    def test_survey_init_success(self):
        """Ensures that /survey_init/ succeeds"""
        data = {
            'course_id': self.course_id,
            'unit_id': self.unit_id,
        }
        req = self.request_factory.post('/survey_init/', data)
        req.user = self.user
        resp = survey_init(req)
        self.assertEquals(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEquals(obj, {
            'success': True,
        })

    def test_survey_init_fail_when_already_submitted(self):
        """Ensures that /survey_init/ fails when survey_submission already exists"""
        submission = SurveySubmissionFactory.create()

        data = {
            'course_id': submission.course_id,
            'unit_id': submission.unit_id,
        }
        req = self.request_factory.post('/survey_init/', data)
        req.user = submission.user
        resp = survey_init(req)
        self.assertEquals(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEquals(obj, {
            'success': False,
            'survey_answer': submission.get_survey_answer(),
        })

    def test_survey_ajax_get_method_not_allowed(self):
        """Ensures that get request to /survey_ajax/ is not allowed"""
        req = self.request_factory.get('/survey_ajax/')
        resp = survey_ajax(req)
        self.assertIsInstance(resp, HttpResponseNotAllowed)

    def test_survey_ajax_with_empty_course_id(self):
        """Ensures that request with empty course_id raises Http404"""
        data = {
            'unit_id': self.unit_id,
            'survey_name': self.survey_name,
            'survey_answer': self.survey_answer,
        }
        req = self.request_factory.post('/survey_ajax/', data)
        req.user = self.user
        self.assertRaises(Http404, survey_ajax, req)

    def test_survey_ajax_with_empty_unit_id(self):
        """Ensures that request with empty unit_id raises Http404"""
        data = {
            'course_id': self.course_id,
            'survey_name': self.survey_name,
            'survey_answer': self.survey_answer,
        }
        req = self.request_factory.post('/survey_ajax/', data)
        req.user = self.user
        self.assertRaises(Http404, survey_ajax, req)

    def test_survey_ajax_with_empty_survey_name(self):
        """Ensures that request with empty survey_name raises Http404"""
        data = {
            'course_id': self.course_id,
            'unit_id': self.unit_id,
            'survey_answer': self.survey_answer,
        }
        req = self.request_factory.post('/survey_ajax/', data)
        req.user = self.user
        self.assertRaises(Http404, survey_ajax, req)

    def test_survey_ajax_with_empty_survey_answer(self):
        """Ensures that request with empty survey_answer raises Http404"""
        data = {
            'course_id': self.course_id,
            'unit_id': self.unit_id,
            'survey_name': self.survey_name,
        }
        req = self.request_factory.post('/survey_ajax/', data)
        req.user = self.user
        self.assertRaises(Http404, survey_ajax, req)

    def test_survey_ajax_success(self):
        """Ensures that /survey_ajax/ succeeds"""
        data = {
            'course_id': self.course_id,
            'unit_id': self.unit_id,
            'survey_name': self.survey_name,
            'survey_answer': self.survey_answer,
        }
        req = self.request_factory.post('/survey_ajax/', data)
        req.user = self.user
        resp = survey_ajax(req)
        self.assertEquals(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEquals(obj, {
            'success': True,
        })
        # assert that SurveySubmission record is created
        submissions = SurveySubmission.objects.filter(
            course_id=self.course_id,
            unit_id=self.unit_id,
            user=self.user
        )
        self.assertEquals(len(submissions), 1)
        self.assertEquals(submissions[0].survey_name, self.survey_name)
        self.assertEquals(submissions[0].survey_answer, self.survey_answer)

    def test_survey_ajax_fail_when_already_submitted(self):
        """Ensures that /survey_ajax/ fails when survey_submission already exists"""
        submission = SurveySubmissionFactory.create()

        data = {
            'course_id': submission.course_id,
            'unit_id': submission.unit_id,
            'survey_name': self.survey_name,
            'survey_answer': self.survey_answer,
        }
        req = self.request_factory.post('/survey_ajax/', data)
        req.user = submission.user
        resp = survey_ajax(req)
        self.assertEquals(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEquals(obj, {
            'success': False,
            'survey_answer': submission.get_survey_answer(),
        })

    def test_survey_ajax_with_unloadable_survey_answer(self):
        """Ensures that request with unloadable survey_answer raises Http404"""
        data = {
            'course_id': self.course_id,
            'unit_id': self.unit_id,
            'survey_name': self.survey_name,
            'survey_answer': 'This cannot be loaded by json.loads',
        }
        req = self.request_factory.post('/survey_ajax/', data)
        req.user = self.user
        self.assertRaises(Http404, survey_ajax, req)

    def test_survey_ajax_with_over_maxlength_survey_answer(self):
        """Ensures that request with over maxlength survey_answer raises Http404"""
        data = {
            'course_id': self.course_id,
            'unit_id': self.unit_id,
            'survey_name': self.survey_name,
            'survey_answer': json.dumps({'Q1': 'a' * 1001})
        }
        req = self.request_factory.post('/survey_ajax/', data)
        req.user = self.user
        self.assertRaises(Http404, survey_ajax, req)

    def test_survey_models_survey_submission(self):
        """Test for survey.models.SurveySubmission get_survey_answer/set_survey_answer"""
        submission = SurveySubmission()
        self.assertEquals(submission.get_survey_answer(), {})
        submission.set_survey_answer({})
        self.assertEquals(submission.get_survey_answer(), {})
