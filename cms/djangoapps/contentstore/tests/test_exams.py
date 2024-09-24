"""
Test the exams service integration into Studio
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock

import ddt
from django.conf import settings
from edx_toggles.toggles.testutils import override_waffle_flag
from zoneinfo import ZoneInfo

from cms.djangoapps.contentstore.signals.handlers import listen_for_course_publish
from openedx.core.djangoapps.course_apps.toggles import EXAMS_IDA
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory


@ddt.ddt
@override_waffle_flag(EXAMS_IDA, active=True)
@patch.dict('django.conf.settings.FEATURES', {'ENABLE_SPECIAL_EXAMS': True})
@patch('cms.djangoapps.contentstore.exams._patch_course_exams')
@patch('cms.djangoapps.contentstore.signals.handlers.transaction.on_commit',
       new=Mock(side_effect=lambda func: func()),)  # run right away
class TestExamService(ModuleStoreTestCase):
    """
    Test for syncing exams to the exam service
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        """
        Initial data setup
        """
        super().setUp()

        self.course = CourseFactory.create(
            org='edX',
            course='900',
            run='test_run',
            enable_proctored_exams=True,
            proctoring_provider='null',
        )
        self.chapter = BlockFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        self.course_key = str(self.course.id)

        # create one non-exam sequence
        chapter2 = BlockFactory.create(parent=self.course, category='chapter', display_name='Test Homework')
        BlockFactory.create(
            parent=chapter2,
            category='sequential',
            display_name='Homework 1',
            graded=True,
            is_time_limited=False,
            due=datetime.now(ZoneInfo("UTC")) + timedelta(minutes=60),
        )

    def _get_exams_url(self, course_id):
        return f'{settings.EXAMS_SERVICE_URL}/exams/course_id/{course_id}/'

    @ddt.data(
        (False, False, False, 'timed'),
        (True, False, False, 'proctored'),
        (True, True, False, 'practice'),
        (True, True, True, 'onboarding'),
    )
    @ddt.unpack
    def test_publishing_exam(self, is_proctored_exam, is_practice_exam,
                             is_onboarding_exam, expected_type, mock_patch_course_exams):
        """
        When a course is published it will register all exams sections with the exams service
        """
        default_time_limit_minutes = 10
        due_date = datetime.now(ZoneInfo("UTC")) + timedelta(minutes=default_time_limit_minutes + 1)

        sequence = BlockFactory.create(
            parent=self.chapter,
            category='sequential',
            display_name='Test Proctored Exam',
            graded=True,
            is_time_limited=True,
            default_time_limit_minutes=default_time_limit_minutes,
            is_proctored_enabled=is_proctored_exam,
            is_practice_exam=is_practice_exam,
            due=due_date,
            hide_after_due=True,
            is_onboarding_exam=is_onboarding_exam,
        )

        expected_exams = [{
            'course_id': self.course_key,
            'content_id': str(sequence.location),
            'exam_name': sequence.display_name,
            'time_limit_mins': sequence.default_time_limit_minutes,
            'due_date': due_date.isoformat(),
            'exam_type': expected_type,
            'is_active': True,
            'hide_after_due': True,
            # backend is only required for edx-proctoring support edx-exams will maintain LTI backends
            'backend': 'null',
        }]
        listen_for_course_publish(self, self.course.id)
        mock_patch_course_exams.assert_called_once_with(expected_exams, self.course_key)

    def test_publish_no_exam(self, mock_patch_course_exams):
        """
        Exam service is called with an empty list if there are no exam sections.
        This will deactivate any currently active exams
        """
        listen_for_course_publish(self, self.course.id)
        mock_patch_course_exams.assert_called_once_with([], self.course_key)

    def test_dangling_exam(self, mock_patch_course_exams):
        """
        Make sure we filter out all dangling items
        """
        BlockFactory.create(
            parent=self.chapter,
            category='sequential',
            display_name='Test Proctored Exam',
            graded=True,
            is_time_limited=True,
            default_time_limit_minutes=10,
            is_proctored_enabled=True,
            hide_after_due=False,
        )
        self.store.delete_item(self.chapter.location, self.user.id)

        listen_for_course_publish(self, self.course.id)
        mock_patch_course_exams.assert_called_once_with([], self.course_key)

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_SPECIAL_EXAMS': False})
    def test_feature_flag_off(self, mock_patch_course_exams):
        """
        Make sure the feature flag is honored
        """
        BlockFactory.create(
            parent=self.chapter,
            category='sequential',
            display_name='Test Proctored Exam',
            graded=True,
            is_time_limited=True,
            default_time_limit_minutes=10,
            is_proctored_enabled=True,
            hide_after_due=False,
        )

        listen_for_course_publish(self, self.course.id)
        mock_patch_course_exams.assert_not_called()

    # MODIFY DUE DATE HERE
    @ddt.data(
        (True, datetime(2035, 1, 1, 0, 0, tzinfo=timezone.utc)),
        (False, datetime(2035, 1, 1, 0, 0, tzinfo=timezone.utc)),
        (True, None),
        (False, None),
    )
    @ddt.unpack
    def test_no_due_dates(self, is_self_paced, course_end_date, mock_patch_course_exams):
        """
        Test that the coures end date is registered as the due date when the subsection does not have a due date for
        both self-paced and instructor-paced exams.
        """
        self.course.self_paced = is_self_paced
        self.course.end = course_end_date
        self.course = self.update_course(self.course, 1)
        BlockFactory.create(
            parent=self.chapter,
            category='sequential',
            display_name='Test Proctored Exam',
            graded=True,
            is_time_limited=True,
            default_time_limit_minutes=60,
            is_proctored_enabled=False,
            is_practice_exam=False,
            due=None,
            hide_after_due=True,
            is_onboarding_exam=False,
        )

        listen_for_course_publish(self, self.course.id)
        called_exams, called_course = mock_patch_course_exams.call_args[0]
        assert called_exams[0]['due_date'] == (course_end_date.isoformat() if course_end_date else None)

    @ddt.data(True, False)
    def test_subsection_due_date_prioritized(self, is_self_paced, mock_patch_course_exams):
        """
        Test that the subsection due date is registered as the due date when both the subsection has a due date and the
        course has an end date for both self-paced and instructor-paced exams.
        """
        self.course.self_paced = is_self_paced
        self.course.end = datetime(2035, 1, 1, 0, 0)
        self.course = self.update_course(self.course, 1)

        sequential_due_date = datetime.now(ZoneInfo("UTC")) + timedelta(minutes=60)
        BlockFactory.create(
            parent=self.chapter,
            category='sequential',
            display_name='Test Proctored Exam',
            graded=True,
            is_time_limited=True,
            default_time_limit_minutes=60,
            is_proctored_enabled=False,
            is_practice_exam=False,
            due=sequential_due_date,
            hide_after_due=True,
            is_onboarding_exam=False,
        )

        listen_for_course_publish(self, self.course.id)
        called_exams, called_course = mock_patch_course_exams.call_args[0]
        assert called_exams[0]['due_date'] == sequential_due_date.isoformat()
