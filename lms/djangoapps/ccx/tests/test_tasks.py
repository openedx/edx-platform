"""
Tests for celery tasks defined in tasks module
"""

from mock_django import mock_signal_receiver

from lms.djangoapps.ccx.tests.factories import CcxFactory
from student.roles import CourseCcxCoachRole
from student.tests.factories import (
    AdminFactory,
)
from xmodule.modulestore.django import SignalHandler
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE)
from openedx.core.djangoapps.content.course_structures.models import CourseStructure
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from ccx_keys.locator import CCXLocator

from lms.djangoapps.ccx.tasks import send_ccx_course_published


class TestSendCCXCoursePublished(ModuleStoreTestCase):
    """unit tests for the send ccx course published task
    """

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        """
        Set up tests
        """
        super(TestSendCCXCoursePublished, self).setUp()
        course = self.course = CourseFactory.create(org="edX", course="999", display_name="Run 666")
        course2 = self.course2 = CourseFactory.create(org="edX", course="999a", display_name="Run 667")
        coach = AdminFactory.create()
        role = CourseCcxCoachRole(course.id)
        role.add_users(coach)
        self.ccx = CcxFactory(course_id=course.id, coach=coach)
        self.ccx2 = CcxFactory(course_id=course.id, coach=coach)
        self.ccx3 = CcxFactory(course_id=course.id, coach=coach)
        self.ccx4 = CcxFactory(course_id=course2.id, coach=coach)

    def call_fut(self, course_key):
        """Call the function under test
        """
        send_ccx_course_published(unicode(course_key))

    def test_signal_not_sent_for_ccx(self):
        """Check that course published signal is not sent when course key is for a ccx
        """
        course_key = CCXLocator.from_course_locator(self.course.id, self.ccx.id)
        with mock_signal_receiver(SignalHandler.course_published) as receiver:
            self.call_fut(course_key)
            self.assertEqual(receiver.call_count, 0)

    def test_signal_sent_for_ccx(self):
        """Check that course published signal is sent when course key is not for a ccx.
        We have 4 ccx's, but only 3 are derived from the course id used here, so call
        count must be 3 to confirm that all derived courses and no more got the signal.
        """
        with mock_signal_receiver(SignalHandler.course_published) as receiver:
            self.call_fut(self.course.id)
            self.assertEqual(receiver.call_count, 3)

    def test_course_structure_generated(self):
        """Check that course structure is generated after course published signal is sent
        """
        ccx_structure = {
            u"blocks": {
                u"ccx-block-v1:edX+999+Run_666+ccx@1+type@course+block@course": {
                    u"block_type": u"course",
                    u"graded": False,
                    u"format": None,
                    u"usage_key": u"ccx-block-v1:edX+999+Run_666+ccx@1+type@course+block@course",
                    u"children": [
                    ],
                    u"display_name": u"Run 666"
                }
            },
            u"root": u"ccx-block-v1:edX+999+Run_666+ccx@1+type@course+block@course"
        }
        course_key = CCXLocator.from_course_locator(self.course.id, self.ccx.id)
        structure = CourseStructure.objects.filter(course_id=course_key)
        # no structure exists before signal is called
        self.assertEqual(len(structure), 0)
        with mock_signal_receiver(SignalHandler.course_published) as receiver:
            self.call_fut(self.course.id)
            self.assertEqual(receiver.call_count, 3)
            structure = CourseStructure.objects.get(course_id=course_key)
            self.assertEqual(structure.structure, ccx_structure)

    def test_course_overview_cached(self):
        """Check that course overview is cached after course published signal is sent
        """
        course_key = CCXLocator.from_course_locator(self.course.id, self.ccx.id)
        overview = CourseOverview.objects.filter(id=course_key)
        self.assertEqual(len(overview), 0)
        with mock_signal_receiver(SignalHandler.course_published) as receiver:
            self.call_fut(self.course.id)
            self.assertEqual(receiver.call_count, 3)
            overview = CourseOverview.objects.filter(id=course_key)
            self.assertEqual(len(overview), 1)
