"""Tests for verifying availability of resources for locking"""


import ddt
import six
from mock import Mock, patch

from cms.djangoapps.contentstore.signals.handlers import GRADING_POLICY_COUNTDOWN_SECONDS, handle_grading_policy_changed
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
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
