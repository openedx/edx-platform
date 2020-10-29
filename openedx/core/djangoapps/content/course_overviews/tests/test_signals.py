

import datetime

import ddt
from mock import patch

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, check_mongo_calls

from ..models import CourseOverview


@ddt.ddt
class CourseOverviewSignalsTestCase(ModuleStoreTestCase):
    """
    Tests for CourseOverview signals.
    """
    ENABLED_SIGNALS = ['course_deleted', 'course_published']
    TODAY = datetime.datetime.utcnow()
    NEXT_WEEK = TODAY + datetime.timedelta(days=7)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_caching(self, modulestore_type):
        """
        Tests that CourseOverview structures are actually getting cached.

        Arguments:
            modulestore_type (ModuleStoreEnum.Type): type of store to create the
                course in.
        """
        # Creating a new course will trigger a publish event and the course will be cached
        course = CourseFactory.create(default_store=modulestore_type, emit_signals=True)

        # The cache will be hit and mongo will not be queried
        with check_mongo_calls(0):
            CourseOverview.get_from_id(course.id)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_cache_invalidation(self, modulestore_type):
        """
        Tests that when a course is published or deleted, the corresponding
        course_overview is removed from the cache.

        Arguments:
            modulestore_type (ModuleStoreEnum.Type): type of store to create the
                course in.
        """
        with self.store.default_store(modulestore_type):

            # Create a course where mobile_available is True.
            course = CourseFactory.create(mobile_available=True, default_store=modulestore_type)
            course_overview_1 = CourseOverview.get_from_id(course.id)
            self.assertTrue(course_overview_1.mobile_available)

            # Set mobile_available to False and update the course.
            # This fires a course_published signal, which should be caught in signals.py, which should in turn
            # delete the corresponding CourseOverview from the cache.
            course.mobile_available = False
            with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
                self.store.update_item(course, ModuleStoreEnum.UserID.test)

            # Make sure that when we load the CourseOverview again, mobile_available is updated.
            course_overview_2 = CourseOverview.get_from_id(course.id)
            self.assertFalse(course_overview_2.mobile_available)

            # Verify that when the course is deleted, the corresponding CourseOverview is deleted as well.
            with self.assertRaises(CourseOverview.DoesNotExist):
                self.store.delete_course(course.id, ModuleStoreEnum.UserID.test)
                CourseOverview.get_from_id(course.id)

    def assert_changed_signal_sent(self, field_name, initial_value, changed_value, mock_signal):
        course = CourseFactory.create(emit_signals=True, **{field_name: initial_value})

        # changing display name doesn't fire the signal
        course.display_name = course.display_name + u'changed'
        self.store.update_item(course, ModuleStoreEnum.UserID.test)
        self.assertFalse(mock_signal.called)

        # changing the given field fires the signal
        setattr(course, field_name, changed_value)
        self.store.update_item(course, ModuleStoreEnum.UserID.test)
        self.assertTrue(mock_signal.called)

    @patch('openedx.core.djangoapps.content.course_overviews.signals.COURSE_START_DATE_CHANGED.send')
    def test_start_changed(self, mock_signal):
        self.assert_changed_signal_sent('start', self.TODAY, self.NEXT_WEEK, mock_signal)

    @patch('openedx.core.djangoapps.content.course_overviews.signals.COURSE_PACING_CHANGED.send')
    def test_pacing_changed(self, mock_signal):
        self.assert_changed_signal_sent('self_paced', True, False, mock_signal)
