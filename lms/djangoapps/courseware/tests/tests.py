'''
Test for lms courseware app
'''
import logging
import json
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
import datetime
from django.utils.timezone import UTC

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


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
                'render_template': 'mitxmako.shortcuts.render_to_string'
            }
        }
    }
    store['direct'] = store['default']
    return store


def draft_mongo_store_config(data_dir):
    '''Defines default module store using DraftMongoModuleStore'''
    return {
        'default': {
            'ENGINE': 'xmodule.modulestore.mongo.DraftMongoModuleStore',
            'OPTIONS': {
                'default_class': 'xmodule.raw_module.RawDescriptor',
                'host': 'localhost',
                'db': 'test_xmodule',
                'collection': 'modulestore_%s' % uuid4().hex,
                'fs_root': data_dir,
                'render_template': 'mitxmako.shortcuts.render_to_string',
            }
        },
        'direct': {
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


def xml_store_config(data_dir):
    '''Defines default module store using XMLModuleStore'''
    return {
        'default': {
            'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
            'OPTIONS': {
                'data_dir': data_dir,
                'default_class': 'xmodule.hidden_module.HiddenDescriptor',
            }
        }
    }

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
TEST_DATA_XML_MODULESTORE = xml_store_config(TEST_DATA_DIR)
TEST_DATA_MONGO_MODULESTORE = mongo_store_config(TEST_DATA_DIR)
TEST_DATA_DRAFT_MONGO_MODULESTORE = draft_mongo_store_config(TEST_DATA_DIR)


class LoginEnrollmentTestCase(TestCase):

    '''
    Base TestCase providing support for user creation,
    activation, login, and course enrollment
    '''

    def assertRedirectsNoFollow(self, response, expected_url):
        """
        http://devblog.point2.com/2010/04/23/djangos-assertredirects-little-gotcha/

        Don't check that the redirected-to page loads--there should be other tests for that.

        Some of the code taken from django.test.testcases.py
        """
        self.assertEqual(response.status_code, 302,
                         'Response status code was %d instead of 302'
                         % (response.status_code))
        url = response['Location']

        e_scheme, e_netloc, e_path, e_query, e_fragment = urlsplit(expected_url)
        if not (e_scheme or e_netloc):
            expected_url = urlunsplit(('http', 'testserver',
                                       e_path, e_query, e_fragment))

        self.assertEqual(url, expected_url,
                         "Response redirected to '%s', expected '%s'" %
                         (url, expected_url))

    def setup_viewtest_user(self):
        '''create a user account, activate, and log in'''
        self.viewtest_email = 'view@test.com'
        self.viewtest_password = 'foo'
        self.viewtest_username = 'viewtest'
        self.create_account(self.viewtest_username,
                            self.viewtest_email, self.viewtest_password)
        self.activate_user(self.viewtest_email)
        self.login(self.viewtest_email, self.viewtest_password)

    # ============ User creation and login ==============

    def _login(self, email, password):
        '''Login.  View should always return 200.  The success/fail is in the
        returned json'''
        resp = self.client.post(reverse('login'),
                                {'email': email, 'password': password})
        self.assertEqual(resp.status_code, 200)
        return resp

    def login(self, email, password):
        '''Login, check that it worked.'''
        resp = self._login(email, password)
        data = parse_json(resp)
        self.assertTrue(data['success'])
        return resp

    def logout(self):
        '''Logout, check that it worked.'''
        resp = self.client.get(reverse('logout'), {})
        # should redirect
        self.assertEqual(resp.status_code, 302)
        return resp

    def _create_account(self, username, email, password):
        '''Try to create an account.  No error checking'''
        resp = self.client.post('/create_account', {
            'username': username,
            'email': email,
            'password': password,
            'name': 'Fred Weasley',
            'terms_of_service': 'true',
            'honor_code': 'true',
        })
        return resp

    def create_account(self, username, email, password):
        '''Create the account and check that it worked'''
        resp = self._create_account(username, email, password)
        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertEqual(data['success'], True)

        # Check both that the user is created, and inactive
        self.assertFalse(get_user(email).is_active)

        return resp

    def _activate_user(self, email):
        '''Look up the activation key for the user, then hit the activate view.
        No error checking'''
        activation_key = get_registration(email).activation_key

        # and now we try to activate
        url = reverse('activate', kwargs={'key': activation_key})
        resp = self.client.get(url)
        return resp

    def activate_user(self, email):
        resp = self._activate_user(email)
        self.assertEqual(resp.status_code, 200)
        # Now make sure that the user is now actually activated
        self.assertTrue(get_user(email).is_active)

    def try_enroll(self, course):
        """Try to enroll.  Return bool success instead of asserting it."""
        resp = self.client.post('/change_enrollment', {
            'enrollment_action': 'enroll',
            'course_id': course.id,
        })
        print ('Enrollment in %s result status code: %s'
               % (course.location.url(), str(resp.status_code)))
        return resp.status_code == 200

    def enroll(self, course):
        """Enroll the currently logged-in user, and check that it worked."""
        result = self.try_enroll(course)
        self.assertTrue(result)

    def unenroll(self, course):
        """Unenroll the currently logged-in user, and check that it worked."""
        resp = self.client.post('/change_enrollment', {
            'enrollment_action': 'unenroll',
            'course_id': course.id,
        })
        self.assertTrue(resp.status_code == 200)

    def check_for_get_code(self, code, url):
        """
        Check that we got the expected code when accessing url via GET.
        Returns the response.
        """
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, code,
                         "got code %d for url '%s'. Expected code %d"
                         % (resp.status_code, url, code))
        return resp

    def check_for_post_code(self, code, url, data={}):
        """
        Check that we got the expected code when accessing url via POST.
        Returns the response.
        """
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, code,
                         "got code %d for url '%s'. Expected code %d"
                         % (resp.status_code, url, code))
        return resp


@override_settings(MODULESTORE=TEST_DATA_DRAFT_MONGO_MODULESTORE)
class TestDraftModuleStore(TestCase):
    def test_get_items_with_course_items(self):
        store = modulestore()

        # fix was to allow get_items() to take the course_id parameter
        store.get_items(Location(None, None, 'vertical', None, None),
                        course_id='abc', depth=0)

        # test success is just getting through the above statement.
        # The bug was that 'course_id' argument was
        # not allowed to be passed in (i.e. was throwing exception)


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestSubmittingProblems(LoginEnrollmentTestCase):
    """Check that a course gets graded properly"""

    # Subclasses should specify the course slug
    course_slug = "UNKNOWN"
    course_when = "UNKNOWN"

    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}

        course_name = "edX/%s/%s" % (self.course_slug, self.course_when)
        self.course = modulestore().get_course(course_name)
        assert self.course, "Couldn't load course %r" % course_name

        # create a test student
        self.student = 'view@test.com'
        self.password = 'foo'
        self.create_account('u1', self.student, self.password)
        self.activate_user(self.student)
        self.enroll(self.course)

        self.student_user = get_user(self.student)

        self.factory = RequestFactory()

    def problem_location(self, problem_url_name):
        return "i4x://edX/{}/problem/{}".format(self.course_slug, problem_url_name)

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
        answer_key_prefix = 'input_i4x-edX-{}-problem-{}_'.format(self.course_slug, problem_url_name)
        resp = self.client.post(modx_url,
            { (answer_key_prefix + k): v for k, v in responses.items() }
            )

        return resp

    def reset_question_answer(self, problem_url_name):
        '''resets specified problem for current user'''
        problem_location = self.problem_location(problem_url_name)
        modx_url = self.modx_url(problem_location, 'problem_reset')
        resp = self.client.post(modx_url)
        return resp


class TestCourseGrader(TestSubmittingProblems):
    """Check that a course gets graded properly"""

    course_slug = "graded"
    course_when = "2012_Fall"

    def get_grade_summary(self):
        '''calls grades.grade for current user and course'''
        model_data_cache = ModelDataCache.cache_for_descriptor_descendents(
            self.course.id, self.student_user, self.course)

        fake_request = self.factory.get(reverse('progress',
                                        kwargs={'course_id': self.course.id}))

        return grades.grade(self.student_user, fake_request,
                            self.course, model_data_cache)

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

    def test_get_graded(self):
        #### Check that the grader shows we have 0% in the course
        self.check_grade_percent(0)

        #### Submit the answers to a few problems as ajax calls
        def earned_hw_scores():
            """Global scores, each Score is a Problem Set"""
            return [s.earned for s in self.get_homework_scores()]

        def score_for_hw(hw_url_name):
            """returns list of scores for a given url"""
            hw_section = [section for section
                          in self.get_progress_summary()[0]['sections']
                          if section.get('url_name') == hw_url_name][0]
            return [s.earned for s in hw_section['scores']]

        # Only get half of the first problem correct
        self.submit_question_answer('H1P1', {'2_1': 'Correct', '2_2': 'Incorrect'})
        self.check_grade_percent(0.06)
        self.assertEqual(earned_hw_scores(), [1.0, 0, 0])  # Order matters
        self.assertEqual(score_for_hw('Homework1'), [1.0, 0.0])

        # Get both parts of the first problem correct
        self.reset_question_answer('H1P1')
        self.submit_question_answer('H1P1', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(0.13)
        self.assertEqual(earned_hw_scores(), [2.0, 0, 0])
        self.assertEqual(score_for_hw('Homework1'), [2.0, 0.0])

        # This problem is shown in an ABTest
        self.submit_question_answer('H1P2', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(0.25)
        self.assertEqual(earned_hw_scores(), [4.0, 0.0, 0])
        self.assertEqual(score_for_hw('Homework1'), [2.0, 2.0])

        # This problem is hidden in an ABTest.
        # Getting it correct doesn't change total grade
        self.submit_question_answer('H1P3', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(0.25)
        self.assertEqual(score_for_hw('Homework1'), [2.0, 2.0])

        # On the second homework, we only answer half of the questions.
        # Then it will be dropped when homework three becomes the higher percent
        # This problem is also weighted to be 4 points (instead of default of 2)
        # If the problem was unweighted the percent would have been 0.38 so we
        # know it works.
        self.submit_question_answer('H2P1', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(0.42)
        self.assertEqual(earned_hw_scores(), [4.0, 4.0, 0])

        # Third homework
        self.submit_question_answer('H3P1', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(0.42)  # Score didn't change
        self.assertEqual(earned_hw_scores(), [4.0, 4.0, 2.0])

        self.submit_question_answer('H3P2', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(0.5)  # Now homework2 dropped. Score changes
        self.assertEqual(earned_hw_scores(), [4.0, 4.0, 4.0])

        # Now we answer the final question (worth half of the grade)
        self.submit_question_answer('FinalQuestion', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(1.0)  # Hooray! We got 100%


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestSchematicResponse(TestSubmittingProblems):
    """Check that we can submit a schematic response, and it answers properly."""

    course_slug = "embedded_python"
    course_when = "2013_Spring"

    def test_schematic(self):
        resp = self.submit_question_answer('schematic_problem',
            { '2_1': json.dumps(
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
            })
        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'correct')

        self.reset_question_answer('schematic_problem')
        resp = self.submit_question_answer('schematic_problem',
            { '2_1': json.dumps(
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
            })
        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'incorrect')

    def test_check_function(self):
        resp = self.submit_question_answer('cfn_problem', {'2_1': "0, 1, 2, 3, 4, 5, 'Outside of loop', 6"})
        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'correct')

        self.reset_question_answer('cfn_problem')

        resp = self.submit_question_answer('cfn_problem', {'2_1': "xyzzy!"})
        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'incorrect')

    def test_computed_answer(self):
        resp = self.submit_question_answer('computed_answer', {'2_1': "Xyzzy"})
        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'correct')

        self.reset_question_answer('computed_answer')

        resp = self.submit_question_answer('computed_answer', {'2_1': "NO!"})
        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'incorrect')
