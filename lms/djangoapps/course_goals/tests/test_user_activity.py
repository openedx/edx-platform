"""
Unit tests for user activity methods.
"""

from datetime import datetime, timedelta
from unittest import mock

import ddt
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test.client import RequestFactory
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_flag
from freezegun import freeze_time
from rest_framework.test import APIClient

from common.djangoapps.edxmako.shortcuts import render_to_response
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.course_goals.models import UserActivity
from lms.djangoapps.course_goals.toggles import POPULATE_USER_ACTIVITY_FLAG
from openedx.core.djangoapps.django_comment_common.models import ForumsConfig
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, TEST_DATA_SPLIT_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

User = get_user_model()


@ddt.ddt
@override_waffle_flag(POPULATE_USER_ACTIVITY_FLAG, active=True)
class UserActivityTests(ModuleStoreTestCase):
    """
    Testing Course Goals User Activity
    """

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create(
            start=datetime(2020, 1, 1),
            end=datetime(2028, 1, 1),
            enrollment_start=datetime(2020, 1, 1),
            enrollment_end=datetime(2028, 1, 1),
            emit_signals=True,
            modulestore=self.store,
            discussion_topics={"Test Topic": {"id": "test_topic"}},
        )
        chapter = ItemFactory(parent=self.course, category='chapter')
        ItemFactory(parent=chapter, category='sequential')

        self.client.login(username=self.user.username, password=self.user_password)
        CourseEnrollment.enroll(self.user, self.course.id)

        self.request = RequestFactory().get('foo')
        self.request.user = self.user

        config = ForumsConfig.current()
        config.enabled = True
        config.save()

    def test_mfe_tabs_call_user_activity(self):
        '''
        New style tabs call one of two metadata endpoints
        These in turn call get_course_tab_list, which populates user activity
        '''
        url = reverse('course-home:course-metadata', args=[self.course.id])
        with mock.patch.object(UserActivity, 'populate_user_activity') as populate_user_activity_mock:
            self.client.get(url)
            populate_user_activity_mock.assert_called_once()

        with mock.patch.object(UserActivity, 'populate_user_activity') as populate_user_activity_mock:
            url = f'/api/courseware/course/{self.course.id}'
            self.client.get(url)
            populate_user_activity_mock.assert_called_once()

    def test_non_mfe_tabs_call_user_activity(self):
        '''
        Tabs that are not yet part of the learning microfrontend all include the course_navigation.html file
        This file calls the get_course_tab_list function, which populates user activity
        '''
        with mock.patch.object(UserActivity, 'populate_user_activity') as populate_user_activity_mock:
            render_to_response('courseware/course_navigation.html', {'course': self.course, 'request': self.request})
            populate_user_activity_mock.assert_called_once()

    def test_when_populate_user_activity_does_not_perform_updates(self):
        '''
        Ensure that populate user activity is not called when:
            1. user or course are not defined
            2. we have already populated user activity for this user/course on this date
            and have a record in the cache
        '''
        with mock.patch.object(cache, 'set', wraps=cache.set) as user_activity_cache_set:
            UserActivity.populate_user_activity(self.user, None)
            user_activity_cache_set.assert_not_called()

            UserActivity.populate_user_activity(None, self.course.id)
            user_activity_cache_set.assert_not_called()

        cache_key = 'goals_user_activity_{}_{}_{}'.format(
            str(self.user.id), str(self.course.id), str(datetime.now().date())
        )
        cache.set(cache_key, 'test', 3600)

        with mock.patch.object(cache, 'set', wraps=cache.set) as user_activity_cache_set:
            UserActivity.populate_user_activity(self.user, self.course.id)
            user_activity_cache_set.assert_not_called()

            # Test that the happy path works to ensure that the measurement in this test isn't broken
            user2 = UserFactory()
            UserActivity.populate_user_activity(user2, self.course.id)
            user_activity_cache_set.assert_called_once()

    def test_that_user_activity_cache_works_properly(self):
        '''
        Ensure that the cache for user activity works properly
            1. user or course are not defined
            2. we have already populated user activity for this user/course on this date
            and have a record in the cache
        '''
        with mock.patch.object(cache, 'set', wraps=cache.set) as user_activity_cache_set:
            UserActivity.populate_user_activity(self.user, self.course.id)
            user_activity_cache_set.assert_called_once()

        with mock.patch.object(cache, 'set', wraps=cache.set) as user_activity_cache_set:
            UserActivity.populate_user_activity(self.user, self.course.id)
            user_activity_cache_set.assert_not_called()

            now_plus_1_day = datetime.now() + timedelta(days=1)
            with freeze_time(now_plus_1_day):
                UserActivity.populate_user_activity(self.user, self.course.id)
                user_activity_cache_set.assert_called_once()

    def test_mobile_argument(self):
        '''
        Method only populates activity if the request is coming from the mobile app
        when the check_if_mobile_app argument is true
        '''
        with mock.patch.object(cache, 'set', wraps=cache.set) as user_activity_cache_set:
            UserActivity.populate_user_activity(
                self.user, self.course.id, request=self.request, check_if_mobile_app=True
            )
            user_activity_cache_set.assert_not_called()

            with mock.patch('lms.djangoapps.course_goals.models.is_request_from_mobile_app', return_value=True):
                UserActivity.populate_user_activity(
                    self.user, self.course.id, request=self.request, check_if_mobile_app=True
                )
                user_activity_cache_set.assert_called_once()

    @ddt.data(
        '/api/course_home/v1/dates/{COURSE_ID}',
        '/api/mobile/v0.5/course_info/{COURSE_ID}/handouts',
        '/api/mobile/v0.5/course_info/{COURSE_ID}/updates',
        '/api/discussion/v1/courses/{COURSE_ID}/',
        '/api/discussion/v1/course_topics/{COURSE_ID}',
        '/api/course_experience/v1/course_deadlines_info/{COURSE_ID}',
        '/api/course_home/v1/dates/{COURSE_ID}',
        '/api/discussion/v1/course_topics/{COURSE_ID}',
        '/api/courseware/course/{COURSE_ID}',
    )
    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def test_mobile_app_user_activity_calls(self, url):
        url = url.replace('{COURSE_ID}', str(self.course.id))
        with mock.patch.object(UserActivity, 'populate_user_activity') as populate_user_activity_mock:
            self.client.get(url)
            populate_user_activity_mock.assert_called_once()

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def test_mobile_app_user_activity_other_calls(self):
        # thread view call
        with mock.patch.object(UserActivity, 'populate_user_activity') as populate_user_activity_mock:
            try:
                self.client.get(reverse("thread-list"), {'course_id': str(self.course.id)})
            except:
                pass
            populate_user_activity_mock.assert_called_once()

        # blocks call
        with mock.patch.object(UserActivity, 'populate_user_activity') as populate_user_activity_mock:
            url = '/api/courses/v2/blocks/'
            self.client.get(url, {'course_id': str(self.course.id), 'username': self.user.username})
            populate_user_activity_mock.assert_called_once()

        # xblock call
        url = '/xblock/' + str(self.course.scope_ids.usage_id)
        try:
            self.client.get(url)
        except:
            pass
        populate_user_activity_mock.assert_called_once()
