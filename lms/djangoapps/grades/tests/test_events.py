"""
Test that various events are fired for models in the grades app.
"""

from unittest import mock

from django.utils.timezone import now
from openedx_events.learning.data import (
    CourseData,
    PersistentCourseGradeData
)
from openedx_events.learning.signals import PERSISTENT_GRADE_SUMMARY_CHANGED
from openedx_events.tests.utils import OpenEdxEventsTestMixin

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.grades.models import PersistentCourseGrade
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class PersistentGradeEventsTest(SharedModuleStoreTestCase, OpenEdxEventsTestMixin):
    """
    Tests for the Open edX Events associated with the persistant grade process through the update_or_create method.

    This class guarantees that the following events are sent during the user updates their grade, with
    the exact Data Attributes as the event definition stated:

        - PERSISTENT_GRADE_SUMMARY_CHANGED: sent after the user updates or creates the grade.
    """
    ENABLED_OPENEDX_EVENTS = [
        "org.openedx.learning.course.persistent_grade_summary.changed.v1",
    ]

    @classmethod
    def setUpClass(cls):
        """
        Set up class method for the Test class.

        This method starts manually events isolation. Explanation here:
        openedx/core/djangoapps/user_authn/views/tests/test_events.py#L44
        """
        super().setUpClass()
        cls.start_events_isolation()

    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create()
        self.params = {
            "user_id": self.user.id,
            "course_id": self.course.id,
            "course_version": self.course.number,
            "course_edited_timestamp": now(),
            "percent_grade": 77.7,
            "letter_grade": "Great job",
            "passed": True,
        }
        self.receiver_called = False

    def _event_receiver_side_effect(self, **kwargs):  # pylint: disable=unused-argument
        """
        Used show that the Open edX Event was called by the Django signal handler.
        """
        self.receiver_called = True

    def test_persistent_grade_event_emitted(self):
        """
        Test whether the persistent grade updated event is sent after the user updates creates or updates their grade.

        Expected result:
            - PERSISTENT_GRADE_SUMMARY_CHANGED is sent and received by the mocked receiver.
            - The arguments that the receiver gets are the arguments sent by the event
            except the metadata generated on the fly.
        """
        event_receiver = mock.Mock(side_effect=self._event_receiver_side_effect)

        PERSISTENT_GRADE_SUMMARY_CHANGED.connect(event_receiver)
        grade = PersistentCourseGrade.update_or_create(**self.params)
        self.assertTrue(self.receiver_called)
        self.assertDictContainsSubset(
            {
                "signal": PERSISTENT_GRADE_SUMMARY_CHANGED,
                "sender": None,
                "grade": PersistentCourseGradeData(
                    user_id=self.params["user_id"],
                    course=CourseData(
                        course_key=self.params["course_id"],
                    ),
                    course_edited_timestamp=self.params["course_edited_timestamp"],
                    course_version=self.params["course_version"],
                    grading_policy_hash='',
                    percent_grade=self.params["percent_grade"],
                    letter_grade=self.params["letter_grade"],
                    passed_timestamp=grade.passed_timestamp
                )
            },
            event_receiver.call_args.kwargs
        )
