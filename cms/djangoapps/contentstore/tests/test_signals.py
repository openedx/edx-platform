"""Tests for verifying availability of resources for locking"""


import datetime
import ddt
import six
from mock import Mock, patch

from cms.djangoapps.contentstore.signals.handlers import GRADING_POLICY_COUNTDOWN_SECONDS, handle_grading_policy_changed
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.views import get_course_enrollments
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
class LockedTest(ModuleStoreTestCase):
    """Test class to verify locking of mocked resources"""

    def setUp(self):
        super(LockedTest, self).setUp()
        self.course = CourseFactory.create(
            org='edx',
            name='course',
            run='run',
        )
        self.user = UserFactory.create()
        CourseEnrollment.enroll(self.user, self.course.id)

    @patch('cms.djangoapps.contentstore.signals.handlers.cache.add')
    @patch('cms.djangoapps.contentstore.signals.handlers.task_compute_all_grades_for_course.apply_async')
    @ddt.data(True, False)
    def test_locked(self, lock_available, compute_grades_async_mock, add_mock):
        add_mock.return_value = lock_available
        sender = Mock()

        handle_grading_policy_changed(sender, course_key=six.text_type(self.course.id))

        cache_key = 'handle_grading_policy_changed-{}'.format(six.text_type(self.course.id))
        self.assertEqual(lock_available, compute_grades_async_mock.called)
        if lock_available:
            add_mock.assert_called_once_with(cache_key, "true", GRADING_POLICY_COUNTDOWN_SECONDS)


@ddt.ddt
class CourseDeletedTestCase(ModuleStoreTestCase):
    """
    Tests for course_deleted signals and side-effects
    """
    ENABLED_SIGNALS = [
        'course_deleted',
        'course_published',
    ]
    TODAY = datetime.datetime.utcnow()
    NEXT_WEEK = TODAY + datetime.timedelta(days=7)

    def setUp(self):
        """
        Add a student & teacher
        """
        super(CourseDeletedTestCase, self).setUp()
        self.student = UserFactory()

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

    def _create_course_with_access_groups(self, course_location, metadata=None, default_store=None):
        """
        Create dummy course with 'CourseFactory' and enroll the student
        """
        metadata = {} if not metadata else metadata
        course = CourseFactory.create(
            org=course_location.org,
            number=course_location.course,
            run=course_location.run,
            metadata=metadata,
            default_store=default_store
        )
        CourseEnrollment.enroll(self.student, course.id)
        return course

    def test_course_listing_errored_deleted_courses(self):
        """
        Create good courses, courses that won't load, and deleted courses which still have
        roles. Test course listing.
        """
        # pylint: disable=protected-access
        mongo_store = modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.mongo)
        good_location = mongo_store.make_course_key('testOrg', 'testCourse', 'RunBabyRun')
        self._create_course_with_access_groups(good_location, default_store=ModuleStoreEnum.Type.mongo)

        course_location = mongo_store.make_course_key('testOrg', 'doomedCourse', 'RunBabyRun')
        self._create_course_with_access_groups(course_location, default_store=ModuleStoreEnum.Type.mongo)
        mongo_store.delete_course(course_location, ModuleStoreEnum.UserID.test)
        courses_list = list(get_course_enrollments(self.student, None, []))
        self.assertEqual(len(courses_list), 1, courses_list)
        self.assertEqual(courses_list[0].course_id, good_location)
