"""
Tests for open ended grading interfaces

django-admin.py test --settings=lms.envs.test --pythonpath=. lms/djangoapps/open_ended_grading
"""

import json
from mock import MagicMock

from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from mitxmako.shortcuts import render_to_string

from xmodule.open_ended_grading_classes import peer_grading_service
from xmodule import peer_grading_module
from xmodule.modulestore.django import modulestore
import xmodule.modulestore.django
from xmodule.x_module import ModuleSystem

from open_ended_grading import staff_grading_service
from courseware.access import _course_staff_group_name
from courseware.tests.tests import LoginEnrollmentTestCase, TEST_DATA_XML_MODULESTORE, get_user

import logging

log = logging.getLogger(__name__)
from django.test.utils import override_settings
from django.http import QueryDict

from xmodule.tests import test_util_open_ended


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestStaffGradingService(LoginEnrollmentTestCase):
    '''
    Check that staff grading service proxy works.  Basically just checking the
    access control and error handling logic -- all the actual work is on the
    backend.
    '''

    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}

        self.student = 'view@test.com'
        self.instructor = 'view2@test.com'
        self.password = 'foo'
        self.location = 'TestLocation'
        self.create_account('u1', self.student, self.password)
        self.create_account('u2', self.instructor, self.password)
        self.activate_user(self.student)
        self.activate_user(self.instructor)

        self.course_id = "edX/toy/2012_Fall"
        self.toy = modulestore().get_course(self.course_id)

        def make_instructor(course):
            group_name = _course_staff_group_name(course.location)
            g = Group.objects.create(name=group_name)
            g.user_set.add(get_user(self.instructor))

        make_instructor(self.toy)

        self.mock_service = staff_grading_service.staff_grading_service()

        self.logout()

    def test_access(self):
        """
        Make sure only staff have access.
        """
        self.login(self.student, self.password)

        # both get and post should return 404
        for view_name in ('staff_grading_get_next', 'staff_grading_save_grade'):
            url = reverse(view_name, kwargs={'course_id': self.course_id})
            self.check_for_get_code(404, url)
            self.check_for_post_code(404, url)


    def test_get_next(self):
        self.login(self.instructor, self.password)

        url = reverse('staff_grading_get_next', kwargs={'course_id': self.course_id})
        data = {'location': self.location}

        r = self.check_for_post_code(200, url, data)

        d = json.loads(r.content)

        self.assertTrue(d['success'])
        self.assertEquals(d['submission_id'], self.mock_service.cnt)
        self.assertIsNotNone(d['submission'])
        self.assertIsNotNone(d['num_graded'])
        self.assertIsNotNone(d['min_for_ml'])
        self.assertIsNotNone(d['num_pending'])
        self.assertIsNotNone(d['prompt'])
        self.assertIsNotNone(d['ml_error_info'])
        self.assertIsNotNone(d['max_score'])
        self.assertIsNotNone(d['rubric'])


    def save_grade_base(self,skip=False):
        self.login(self.instructor, self.password)

        url = reverse('staff_grading_save_grade', kwargs={'course_id': self.course_id})

        data = {'score': '12',
                'feedback': 'great!',
                'submission_id': '123',
                'location': self.location,
                'submission_flagged': "true",
                'rubric_scores[]': ['1', '2']}
        if skip:
            data.update({'skipped' : True})

        r = self.check_for_post_code(200, url, data)
        d = json.loads(r.content)
        self.assertTrue(d['success'], str(d))
        self.assertEquals(d['submission_id'], self.mock_service.cnt)

    def test_save_grade(self):
        self.save_grade_base(skip=False)

    def test_save_grade_skip(self):
        self.save_grade_base(skip=True)

    def test_get_problem_list(self):
        self.login(self.instructor, self.password)

        url = reverse('staff_grading_get_problem_list', kwargs={'course_id': self.course_id})
        data = {}

        r = self.check_for_post_code(200, url, data)
        d = json.loads(r.content)

        self.assertTrue(d['success'], str(d))
        self.assertIsNotNone(d['problem_list'])


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestPeerGradingService(LoginEnrollmentTestCase):
    '''
    Check that staff grading service proxy works.  Basically just checking the
    access control and error handling logic -- all the actual work is on the
    backend.
    '''

    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}

        self.student = 'view@test.com'
        self.instructor = 'view2@test.com'
        self.password = 'foo'
        self.location = 'TestLocation'
        self.create_account('u1', self.student, self.password)
        self.create_account('u2', self.instructor, self.password)
        self.activate_user(self.student)
        self.activate_user(self.instructor)

        self.course_id = "edX/toy/2012_Fall"
        self.toy = modulestore().get_course(self.course_id)
        location = "i4x://edX/toy/peergrading/init"
        model_data = {'data': "<peergrading/>"}
        self.mock_service = peer_grading_service.MockPeerGradingService()
        self.system = ModuleSystem(
            ajax_url=location,
            track_function=None,
            get_module=None,
            render_template=render_to_string,
            replace_urls=None,
            xblock_model_data={},
            s3_interface=test_util_open_ended.S3_INTERFACE,
            open_ended_grading_interface=test_util_open_ended.OPEN_ENDED_GRADING_INTERFACE
        )
        self.descriptor = peer_grading_module.PeerGradingDescriptor(self.system, location, model_data)
        model_data = {}
        self.peer_module = peer_grading_module.PeerGradingModule(self.system, location, self.descriptor, model_data)
        self.peer_module.peer_gs = self.mock_service
        self.logout()

    def test_get_next_submission_success(self):
        data = {'location': self.location}

        r = self.peer_module.get_next_submission(data)
        d = r

        self.assertTrue(d['success'])
        self.assertIsNotNone(d['submission_id'])
        self.assertIsNotNone(d['prompt'])
        self.assertIsNotNone(d['submission_key'])
        self.assertIsNotNone(d['max_score'])

    def test_get_next_submission_missing_location(self):
        data = {}
        d = self.peer_module.get_next_submission(data)
        self.assertFalse(d['success'])
        self.assertEqual(d['error'], "Missing required keys: location")

    def test_save_grade_success(self):
        data = {
            'rubric_scores[]': [0, 0],
            'location': self.location,
            'submission_id': 1,
            'submission_key': 'fake key',
            'score': 2,
            'feedback': 'feedback',
            'submission_flagged': 'false'
        }

        qdict = MagicMock()

        def fake_get_item(key):
            return data[key]

        qdict.__getitem__.side_effect = fake_get_item
        qdict.getlist = fake_get_item
        qdict.keys = data.keys

        r = self.peer_module.save_grade(qdict)
        d = r

        self.assertTrue(d['success'])

    def test_save_grade_missing_keys(self):
        data = {}
        d = self.peer_module.save_grade(data)
        self.assertFalse(d['success'])
        self.assertTrue(d['error'].find('Missing required keys:') > -1)

    def test_is_calibrated_success(self):
        data = {'location': self.location}
        r = self.peer_module.is_student_calibrated(data)
        d = r

        self.assertTrue(d['success'])
        self.assertTrue('calibrated' in d)

    def test_is_calibrated_failure(self):
        data = {}
        d = self.peer_module.is_student_calibrated(data)
        self.assertFalse(d['success'])
        self.assertFalse('calibrated' in d)

    def test_show_calibration_essay_success(self):
        data = {'location': self.location}

        r = self.peer_module.show_calibration_essay(data)
        d = r

        self.assertTrue(d['success'])
        self.assertIsNotNone(d['submission_id'])
        self.assertIsNotNone(d['prompt'])
        self.assertIsNotNone(d['submission_key'])
        self.assertIsNotNone(d['max_score'])

    def test_show_calibration_essay_missing_key(self):
        data = {}

        d = self.peer_module.show_calibration_essay(data)

        self.assertFalse(d['success'])
        self.assertEqual(d['error'], "Missing required keys: location")

    def test_save_calibration_essay_success(self):
        data = {
            'rubric_scores[]': [0, 0],
            'location': self.location,
            'submission_id': 1,
            'submission_key': 'fake key',
            'score': 2,
            'feedback': 'feedback',
            'submission_flagged': 'false'
        }

        qdict = MagicMock()

        def fake_get_item(key):
            return data[key]

        qdict.__getitem__.side_effect = fake_get_item
        qdict.getlist = fake_get_item
        qdict.keys = data.keys

        d = self.peer_module.save_calibration_essay(qdict)
        self.assertTrue(d['success'])
        self.assertTrue('actual_score' in d)

    def test_save_calibration_essay_missing_keys(self):
        data = {}
        d = self.peer_module.save_calibration_essay(data)
        self.assertFalse(d['success'])
        self.assertTrue(d['error'].find('Missing required keys:') > -1)
        self.assertFalse('actual_score' in d)
