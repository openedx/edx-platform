# -*- coding: utf-8 -*-

import datetime

import mock

from openedx.core.djangoapps.schedules.config import COURSE_UPDATE_WAFFLE_FLAG
from openedx.core.djangoapps.schedules.content_highlights import (
    course_has_highlights, get_week_highlights, get_next_section_highlights,
)
from openedx.core.djangoapps.schedules.exceptions import CourseUpdateDoesNotExist
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@skip_unless_lms
class TestContentHighlights(ModuleStoreTestCase):
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        super(TestContentHighlights, self).setUp()
        self._setup_course()
        self._setup_user()

    def _setup_course(self):
        self.course = CourseFactory.create(
            highlights_enabled_for_messaging=True
        )
        self.course_key = self.course.id

    def _setup_user(self):
        self.user = UserFactory.create()
        CourseEnrollment.enroll(self.user, self.course_key)

    def _create_chapter(self, **kwargs):
        ItemFactory.create(
            parent=self.course,
            category='chapter',
            **kwargs
        )

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    def test_non_existent_course_raises_exception(self):
        nonexistent_course_key = self.course_key.replace(run='no_such_run')
        with self.assertRaises(CourseUpdateDoesNotExist):
            get_week_highlights(self.user, nonexistent_course_key, week_num=1)

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    def test_empty_course_raises_exception(self):
        with self.assertRaises(CourseUpdateDoesNotExist):
            get_week_highlights(self.user, self.course_key, week_num=1)

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, False)
    def test_flag_disabled(self):
        with self.store.bulk_operations(self.course_key):
            self._create_chapter(highlights=[u'highlights'])

        self.assertFalse(course_has_highlights(self.course_key))
        with self.assertRaises(CourseUpdateDoesNotExist):
            get_week_highlights(self.user, self.course_key, week_num=1)

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    def test_flag_enabled(self):
        highlights = [u'highlights']
        with self.store.bulk_operations(self.course_key):
            self._create_chapter(highlights=highlights)
        self.assertTrue(course_has_highlights(self.course_key))
        self.assertEqual(
            get_week_highlights(self.user, self.course_key, week_num=1),
            highlights,
        )

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    def test_highlights_disabled_for_messaging(self):
        highlights = [u'A test highlight.']
        with self.store.bulk_operations(self.course_key):
            self._create_chapter(highlights=highlights)
            self.course.highlights_enabled_for_messaging = False
            self.store.update_item(self.course, self.user.id)

        self.assertFalse(course_has_highlights(self.course_key))

        with self.assertRaises(CourseUpdateDoesNotExist):
            get_week_highlights(
                self.user,
                self.course_key,
                week_num=1,
            )

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    def test_course_with_no_highlights(self):
        with self.store.bulk_operations(self.course_key):
            self._create_chapter(display_name=u"Week 1")
            self._create_chapter(display_name=u"Week 2")

        self.course = self.store.get_course(self.course_key)
        self.assertEqual(len(self.course.get_children()), 2)

        self.assertFalse(course_has_highlights(self.course_key))
        with self.assertRaises(CourseUpdateDoesNotExist):
            get_week_highlights(self.user, self.course_key, week_num=1)

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    def test_course_with_highlights(self):
        with self.store.bulk_operations(self.course_key):
            self._create_chapter(highlights=[u'a', u'b', u'á'])
            self._create_chapter(highlights=[])
            self._create_chapter(highlights=[u'skipped a week'])

        self.assertTrue(course_has_highlights(self.course_key))

        self.assertEqual(
            get_week_highlights(self.user, self.course_key, week_num=1),
            [u'a', u'b', u'á'],
        )
        self.assertEqual(
            get_week_highlights(self.user, self.course_key, week_num=2),
            [u'skipped a week'],
        )
        with self.assertRaises(CourseUpdateDoesNotExist):
            get_week_highlights(self.user, self.course_key, week_num=3)

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    def test_staff_only(self):
        with self.store.bulk_operations(self.course_key):
            self._create_chapter(
                highlights=[u"I'm a secret!"],
                visible_to_staff_only=True,
            )

        self.assertTrue(course_has_highlights(self.course_key))
        with self.assertRaises(CourseUpdateDoesNotExist):
            get_week_highlights(self.user, self.course_key, week_num=1)

    @override_waffle_flag(COURSE_UPDATE_WAFFLE_FLAG, True)
    @mock.patch('openedx.core.djangoapps.course_date_signals.utils.get_expected_duration')
    def test_get_next_section_highlights(self, mock_duration):
        mock_duration.return_value = datetime.timedelta(days=2)
        yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        today = datetime.datetime.utcnow()
        tomorrow = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        with self.store.bulk_operations(self.course_key):
            self._create_chapter(  # Week 1
                highlights=[u'a', u'b', u'á'],
            )
            self._create_chapter(  # Week 2
                highlights=[u'skipped a week'],
            )

        self.assertEqual(
            get_next_section_highlights(self.user, self.course_key, yesterday, today.date()),
            ([u'skipped a week'], 2),
        )
        with self.assertRaises(CourseUpdateDoesNotExist):
            get_next_section_highlights(self.user, self.course_key, yesterday, tomorrow.date())
