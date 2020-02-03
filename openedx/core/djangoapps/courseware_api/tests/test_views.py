"""
Tests for courseware API
"""
from datetime import datetime
import unittest
import ddt
import mock

from django.conf import settings

from xmodule.modulestore.django import modulestore

from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_SPLIT_MODULESTORE,
    SharedModuleStoreTestCase
)
from xmodule.modulestore.tests.factories import ItemFactory, ToyCourseFactory
from student.tests.factories import UserFactory
from student.models import CourseEnrollment


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
    @ddt.data(
        (True, None, False),
        (True, 'audit', False),
        (True, 'verified', False),
        (False, None, False),
        (False, None, True),
    )
    @ddt.unpack
    def test_course_metadata(self, logged_in, enrollment_mode, enable_anonymous):
        allow_public_access = mock.Mock()
        allow_public_access.return_value = enable_anonymous
        with mock.patch('openedx.core.djangoapps.courseware_api.views.allow_public_access', allow_public_access):
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
                assert len(response.data['tabs']) == 4
            elif enable_anonymous and not logged_in:
                allow_public_access.assert_called_once()
                assert response.data['enrollment']['mode'] is None
                assert response.data['user_has_access']
            else:
                assert not response.data['user_has_access']


class SequenceApiTestViews(BaseCoursewareTests):
    """
    Tests for the sequence REST API
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chapter = ItemFactory(parent=cls.course, category='chapter')
        cls.sequence = ItemFactory(parent=chapter, category='sequential', display_name='sequence')
        ItemFactory.create(parent=cls.sequence, category='vertical', display_name="Vertical")
        cls.url = '/api/courseware/sequence/{}'.format(cls.sequence.location)

    @classmethod
    def tearDownClass(cls):
        cls.store.delete_item(cls.sequence.location, cls.user.id)
        super().tearDownClass()

    def test_sequence_metadata(self):
        print(self.url)
        print(self.course.location)
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data['display_name'] == 'sequence'
        assert len(response.data['items']) == 1
