"""
Test audit user's access to various content based on content-gating features.
"""

import ddt
from django.http import Http404
from django.test.client import RequestFactory
from django.test.utils import override_settings
from mock import Mock, patch

from course_modes.tests.factories import CourseModeFactory
from courseware.access_response import IncorrectPartitionGroupError
from lms.djangoapps.courseware.module_render import load_single_xblock
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from openedx.features.course_duration_limits.config import CONTENT_TYPE_GATING_FLAG
from student.tests.factories import AdminFactory, CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@ddt.ddt
@override_waffle_flag(CONTENT_TYPE_GATING_FLAG, True)
@override_settings(FIELD_OVERRIDE_PROVIDERS=(
    'openedx.features.content_type_gating.field_override.ContentTypeGatingFieldOverride',
))
class TestProblemTypeAccess(SharedModuleStoreTestCase):

    PROBLEM_TYPES = ['problem', 'openassessment', 'drag-and-drop-v2', 'done', 'edx_sga', ]

    @classmethod
    def setUpClass(self):
        super(TestProblemTypeAccess, self).setUpClass()
        self.factory = RequestFactory()
        self.course = CourseFactory.create(run='testcourse1', display_name='Test Course Title')
        CourseModeFactory.create(course_id=self.course.id, mode_slug='audit')
        CourseModeFactory.create(course_id=self.course.id, mode_slug='verified')
        with self.store.bulk_operations(self.course.id):
            self.chapter = ItemFactory.create(
                parent=self.course,
                display_name='Overview'
            )
            self.welcome = ItemFactory.create(
                parent=self.chapter,
                display_name='Welcome'
            )
            ItemFactory.create(
                parent=self.course,
                category='chapter',
                display_name='Week 1'
            )
            self.chapter_subsection = ItemFactory.create(
                parent=self.chapter,
                category='sequential',
                display_name='Lesson 1'
            )
            chapter_vertical = ItemFactory.create(
                parent=self.chapter_subsection,
                category='vertical',
                display_name='Lesson 1 Vertical - Unit 1'
            )
            self.problem_dict = {}
            for prob_type in self.PROBLEM_TYPES:
                block = ItemFactory.create(
                    parent=chapter_vertical,
                    category=prob_type,
                    display_name=prob_type,
                    graded=True,
                )
                self.problem_dict[prob_type] = block

    def setUp(self):
        super(TestProblemTypeAccess, self).setUp()
        self.audit_user = UserFactory.create()
        self.enrollment = CourseEnrollmentFactory.create(user=self.audit_user, course_id=self.course.id, mode='audit')

    @ddt.data(
        *PROBLEM_TYPES
    )
    def test_audit_fails_access_graded_problems(self, prob_type):
        fake_request = Mock()
        with patch.object(IncorrectPartitionGroupError, '__init__',
                          wraps=IncorrectPartitionGroupError.__init__) as mock_access_error:
            mock_access_error.return_value = IncorrectPartitionGroupError
            with self.assertRaises(Http404):
                load_single_xblock(
                    request=fake_request,
                    user_id=self.audit_user.id,
                    course_id=unicode(self.course.id),
                    usage_key_string=unicode(self.problem_dict[prob_type].scope_ids.usage_id),
                    course=None
                )
            self.assertTrue(mock_access_error.called)
