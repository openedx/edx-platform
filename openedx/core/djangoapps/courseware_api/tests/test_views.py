"""
Tests for courseware API
"""
import unittest
from datetime import datetime

import ddt
import mock
from completion.test_utils import CompletionWaffleTestMixin, submit_completions_for_testing
from django.conf import settings

from lms.djangoapps.courseware.access_utils import ACCESS_DENIED, ACCESS_GRANTED
from lms.djangoapps.courseware.tabs import ExternalLinkCourseTab
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import ItemFactory, ToyCourseFactory


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class BaseCoursewareTests(SharedModuleStoreTestCase):
    """
    Base class for courseware API tests
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.store = modulestore()
        cls.course = ToyCourseFactory.create(
            end=datetime(2028, 1, 1, 1, 1, 1),
            enrollment_start=datetime(2020, 1, 1, 1, 1, 1),
            enrollment_end=datetime(2028, 1, 1, 1, 1, 1),
            emit_signals=True,
            modulestore=cls.store,
        )
        cls.chapter = ItemFactory(parent=cls.course, category='chapter')
        cls.sequence = ItemFactory(parent=cls.chapter, category='sequential', display_name='sequence')
        cls.unit = ItemFactory.create(parent=cls.sequence, category='vertical', display_name="Vertical")

        cls.user = UserFactory(
            username='student',
            email=u'user@example.com',
            password='foo',
            is_staff=False
        )
        cls.url = '/api/courseware/course/{}'.format(cls.course.id)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.store.delete_course(cls.course.id, cls.user.id)

    def setUp(self):
        super().setUp()
        self.client.login(username=self.user.username, password='foo')


@ddt.ddt
class CourseApiTestViews(BaseCoursewareTests):
    """
    Tests for the courseware REST API
    """
    @classmethod
    def setUpClass(cls):
        BaseCoursewareTests.setUpClass()
        cls.course.tabs.append(ExternalLinkCourseTab.load('external_link', name='Zombo', link='http://zombo.com'))
        cls.course.tabs.append(
            ExternalLinkCourseTab.load('external_link', name='Hidden', link='http://hidden.com', is_hidden=True)
        )
        cls.store.update_item(cls.course, cls.user.id)

    @ddt.data(
        (True, None, ACCESS_DENIED),
        (True, 'audit', ACCESS_DENIED),
        (True, 'verified', ACCESS_DENIED),
        (False, None, ACCESS_DENIED),
        (False, None, ACCESS_GRANTED),
    )
    @ddt.unpack
    def test_course_metadata(self, logged_in, enrollment_mode, enable_anonymous):
        check_public_access = mock.Mock()
        check_public_access.return_value = enable_anonymous
        with mock.patch('lms.djangoapps.courseware.access_utils.check_public_access', check_public_access):
            if not logged_in:
                self.client.logout()
            if enrollment_mode:
                CourseEnrollment.enroll(self.user, self.course.id, enrollment_mode)
            response = self.client.get(self.url)
            assert response.status_code == 200
            if enrollment_mode:
                enrollment = response.data['enrollment']
                assert enrollment_mode == enrollment['mode']
                assert enrollment['is_active']
                assert len(response.data['tabs']) == 5
                found = False
                for tab in response.data['tabs']:
                    if tab['type'] == 'external_link':
                        assert tab['url'] != 'http://hidden.com', "Hidden tab is not hidden"
                        if tab['url'] == 'http://zombo.com':
                            found = True
                assert found, 'external link not in course tabs'
            elif enable_anonymous and not logged_in:
                # multiple checks use this handler
                check_public_access.assert_called()
                assert response.data['enrollment']['mode'] is None
                assert response.data['can_load_courseware']['has_access']
            else:
                assert not response.data['can_load_courseware']['has_access']


class SequenceApiTestViews(BaseCoursewareTests):
    """
    Tests for the sequence REST API
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = '/api/courseware/sequence/{}'.format(cls.sequence.location)

    @classmethod
    def tearDownClass(cls):
        cls.store.delete_item(cls.sequence.location, cls.user.id)
        super().tearDownClass()

    def test_sequence_metadata(self):
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data['display_name'] == 'sequence'
        assert len(response.data['items']) == 1


class ResumeApiTestViews(BaseCoursewareTests, CompletionWaffleTestMixin):
    """
    Tests for the resume API
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = '/api/courseware/resume/{}'.format(cls.course.id)

    def test_resume_no_completion(self):
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data['block_id'] is None
        assert response.data['unit_id'] is None
        assert response.data['section_id'] is None

    def test_resume_with_completion(self):
        self.override_waffle_switch(True)
        submit_completions_for_testing(self.user, [self.unit.location])
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data['block_id'] == str(self.unit.location)
        assert response.data['unit_id'] == str(self.unit.location)
        assert response.data['section_id'] == str(self.sequence.location)
