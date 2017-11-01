# -*- coding: utf-8 -*-
import datetime
from unittest import skipUnless

import ddt
from django.conf import settings
from mock import patch, DEFAULT, Mock

from openedx.core.djangoapps.schedules.resolvers import (
    BinnedSchedulesBaseResolver, get_week_highlights, course_has_highlights
)
from openedx.core.djangoapps.schedules.config import COURSE_UPDATE_WAFFLE_FLAG
from openedx.core.djangoapps.schedules.exceptions import CourseUpdateDoesNotExist
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory, SiteConfigurationFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag

from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from student.tests.factories import UserFactory
from student.models import CourseEnrollment


@ddt.ddt
@skip_unless_lms
@skipUnless('openedx.core.djangoapps.schedules.apps.SchedulesConfig' in settings.INSTALLED_APPS,
            "Can't test schedules if the app isn't installed")
class TestBinnedSchedulesBaseResolver(CacheIsolationTestCase):
    def setUp(self):
        super(TestBinnedSchedulesBaseResolver, self).setUp()

        self.site = SiteFactory.create()
        self.site_config = SiteConfigurationFactory(site=self.site)
        self.schedule_config = ScheduleConfigFactory.create(site=self.site)
        self.resolver = BinnedSchedulesBaseResolver(
            async_send_task=Mock(name='async_send_task'),
            site=self.site,
            target_datetime=datetime.datetime.now(),
            day_offset=3,
            bin_num=2,
        )

    @ddt.data(
        'course1'
    )
    def test_get_course_org_filter_equal(self, course_org_filter):
        self.site_config.values['course_org_filter'] = course_org_filter
        self.site_config.save()
        mock_query = Mock()
        result = self.resolver.filter_by_org(mock_query)
        self.assertEqual(result, mock_query.filter.return_value)
        mock_query.filter.assert_called_once_with(enrollment__course__org=course_org_filter)

    @ddt.unpack
    @ddt.data(
        (['course1', 'course2'], ['course1', 'course2'])
    )
    def test_get_course_org_filter_include__in(self, course_org_filter, expected_org_list):
        self.site_config.values['course_org_filter'] = course_org_filter
        self.site_config.save()
        mock_query = Mock()
        result = self.resolver.filter_by_org(mock_query)
        self.assertEqual(result, mock_query.filter.return_value)
        mock_query.filter.assert_called_once_with(enrollment__course__org__in=expected_org_list)

    @ddt.unpack
    @ddt.data(
        (None, set([])),
        ('course1', set([u'course1'])),
        (['course1', 'course2'], set([u'course1', u'course2']))
    )
    def test_get_course_org_filter_exclude__in(self, course_org_filter, expected_org_list):
        SiteConfigurationFactory.create(
            values={'course_org_filter': course_org_filter},
        )
        mock_query = Mock()
        result = self.resolver.filter_by_org(mock_query)
        mock_query.exclude.assert_called_once_with(enrollment__course__org__in=expected_org_list)
        self.assertEqual(result, mock_query.exclude.return_value)


@skip_unless_lms
@skipUnless('openedx.core.djangoapps.schedules.apps.SchedulesConfig' in settings.INSTALLED_APPS,
            "Can't test schedules if the app isn't installed")
class TestGetWeekHighlights(ModuleStoreTestCase):
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        super(TestGetWeekHighlights, self).setUp()
        # Basic course
        self.course = CourseFactory.create()
        self.course_key = self.course.id

        # Users
        self.enrolled_student = UserFactory(username='enrolled')
        CourseEnrollment.enroll(self.enrolled_student, self.course_key)
        self.unenrolled_student = UserFactory(username='unenrolled')

    def test_no_course_or_course_flag_off(self):
        with self.assertRaises(CourseUpdateDoesNotExist):
            get_week_highlights(self.enrolled_student, self.course_key, 1)

        bad_course_key = self.course_key.replace(run='no_such_run')
        with self.assertRaises(CourseUpdateDoesNotExist):
            get_week_highlights(self.enrolled_student, bad_course_key, 1)

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    def test_course_with_no_highlights(self):
        with self.store.bulk_operations(self.course_key):
            ItemFactory.create(
                parent=self.course,
                display_name="Intro Week",
                category='chapter'
            )
            ItemFactory.create(
                parent=self.course,
                display_name="Week 1",
                category='chapter'
            )

        # Update course and fetch it back just to make sure our modulestore
        # changes actually went through.
        self.store.update_item(self.course, self.enrolled_student.id)
        self.course = self.store.get_course(self.course_key)
        self.assertEqual(len(self.course.get_children()), 2)

        # We entered no highlights for any week.
        self.assertFalse(course_has_highlights(self.course_key))

        with self.assertRaises(CourseUpdateDoesNotExist):
            get_week_highlights(self.enrolled_student, self.course_key, 1)

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    def test_course_with_highlights(self):
        with self.store.bulk_operations(self.course_key):
            ItemFactory.create(
                parent=self.course,
                display_name="Week 1",
                category='chapter',
                highlights=[]
            )
            ItemFactory.create(
                parent=self.course,
                display_name="Week 2",
                category='chapter',
                highlights=[u'A', u'B', u'á']
            )
            ItemFactory.create(
                parent=self.course,
                display_name="Week 3",
                category='chapter',
                highlights=["I'm a secret!"]
            )

        self.store.update_item(self.course, self.enrolled_student.id)

        # Generic check for highlights existing
        self.assertTrue(course_has_highlights(self.course_key))

        # Getting highlights for the week that has them.
        self.assertEqual(
            get_week_highlights(self.enrolled_student, self.course_key, 2),
            [u'A', u'B', u'á'],
        )

        # Getting highlights for the week that doesn't have them.
        with self.assertRaises(CourseUpdateDoesNotExist):
            get_week_highlights(self.enrolled_student, self.course_key, 1)

        # Getting highlights for a user that can't access that week (e.g. they
        # unenrolled).
        with self.assertRaises(CourseUpdateDoesNotExist):
            get_week_highlights(self.unenrolled_student, self.course_key, 2)

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    def test_access_permissions(self):
        with self.store.bulk_operations(self.course_key):
            # Staff-only Chapter
            ItemFactory.create(
                parent=self.course,
                visible_to_staff_only=True,
                display_name="Hidden Week",
                category='chapter',
                highlights=["I'm a secret!"]
            )
        self.store.update_item(self.course, self.enrolled_student.id)

        # Staff-only is sometimes used as a staging area for content that will
        # go live, so still count it as a course with highlights even if those
        # highlights only exist in staff-only chapters.
        self.assertTrue(course_has_highlights(self.course_key))

        # But we shouldn't be able to access those highlights as a student.
        with self.assertRaises(CourseUpdateDoesNotExist):
            get_week_highlights(self.enrolled_student, self.course_key, 1)
