"""
Test Assessment Helpers.
"""
from datetime import datetime, timedelta

import mock
import pytest
from ddt import data, ddt, unpack
from django.contrib.auth.models import User
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import BlockUsageLocator
from pytz import UTC
from submissions.models import Score

from openassessment.assessment.models import Assessment, AssessmentPart
from openassessment.workflow import api as workflow_api
from openassessment.workflow.models import AssessmentWorkflow
from openedx.features.assessment import helpers
from openedx.features.assessment.constants import NO_PENDING_ORA
from openedx.features.assessment.tests.factories import StudentItemFactory, SubmissionFactory
from openedx.features.philu_utils.tests.mixins import CourseAssessmentMixin
from student.tests.factories import AnonymousUserIdFactory, CourseEnrollmentFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from .constants import PHILU_BOT_NAME, THREE_POINT_RUBRIC_DICTIONARY, TWO_POINT_RUBRIC_DICTIONARY


@ddt
@pytest.mark.django_db
class AssessmentHelperModuleStoreTestCase(CourseAssessmentMixin, ModuleStoreTestCase):
    """
    Assessment helper unit tests which require module store.
    """

    def setUp(self):
        """
        Create a course with specific xblocks.
        """
        super(AssessmentHelperModuleStoreTestCase, self).setUp()

        xblock_types = ['openassessment', 'html', 'openassessment', 'openassessment']
        self.source_course = CourseFactory.create(
            modulestore=self.store,
            emit_signals=False
        )

        self.create_course_chapter_with_specific_xblocks(self.store, self.source_course, xblock_types)

        self.all_ora_in_course = modulestore().get_items(
            self.source_course.id,
            qualifiers={'category': 'openassessment'}
        )

    def _create_enrollment_submission(self, submission_date, course_id, canceled_one_submission=False,
                                      exclude_submissions=False):
        """
        A helper function for tests, which create course enrollment, and perform submission for ORAs in course.
        """
        enrollment = CourseEnrollmentFactory(course_id=course_id)
        anonymous_user = AnonymousUserIdFactory(course_id=course_id, user=enrollment.user)

        submissions = []
        submission_uuids = []

        if exclude_submissions:
            return enrollment, submissions, submission_uuids

        for open_assessment in self.all_ora_in_course:
            submission = SubmissionFactory(
                student_item__student_id=anonymous_user.anonymous_user_id,
                student_item__course_id=course_id,
                student_item__item_id=open_assessment.location,
                created_at=submission_date,
            )
            submissions.append(submission)
            submission_uuids.append(submission.uuid)

        if canceled_one_submission:
            # Lets consider last submission is in canceled state, so it should not auto score
            submission_uuids.pop()
            submissions.pop()

        return enrollment, submissions, submission_uuids

    @mock.patch('openedx.features.assessment.helpers.autoscore_ora_submission')
    @mock.patch('openedx.features.assessment.helpers._log_multiple_submissions_info')
    @mock.patch('openedx.features.assessment.helpers._get_submissions_to_autoscore_by_enrollment')
    @mock.patch('openedx.features.assessment.helpers.configuration_helpers.get_value')
    def test_find_and_autoscore_submissions_successfully(self, mock_get_value, mock_get_submissions_by_enrollment,
                                                         mock_log_multiple_submissions_info,
                                                         mock_autoscore_ora_submission):
        """
        Verify that all ORA submissions corresponded to provided enrollments and submission uuids. Also check autoscore
        function called for each resulting submission.
        """
        mock_get_value.return_value = 3
        enrollment1, submissions1, uuid_list_1 = self._create_enrollment_submission(
            datetime(2019, 12, 30, tzinfo=UTC).date(),
            course_id=self.source_course.id,
            canceled_one_submission=True
        )
        enrollment2, submissions2, uuid_list_2 = self._create_enrollment_submission(
            datetime(2020, 1, 1, tzinfo=UTC).date(), course_id=self.source_course.id,
        )
        mock_get_submissions_by_enrollment.side_effect = [submissions1, submissions2]
        enrollment = [enrollment1, enrollment2, ]
        submissions = submissions1 + submissions2
        submission_uuids = uuid_list_1 + uuid_list_2
        delta_date = datetime.now(UTC).date() - timedelta(days=3)

        helpers.find_and_autoscore_submissions(enrollment, submission_uuids)

        mock_log_multiple_submissions_info.assert_called_once_with(submissions, 3, delta_date)
        self.assertEqual(mock_autoscore_ora_submission.call_count, len(submissions))

    @data(
        datetime(2019, 12, 30, tzinfo=UTC).date(),
        datetime(2020, 1, 1, tzinfo=UTC).date(),
        datetime(2020, 1, 2, tzinfo=UTC).date(),
    )
    def test_get_submissions_to_autoscore_by_enrollment_successfully(self, submission_date):
        """
        Verify ORA submissions, for a specific enrollment, which correspond to provided submission uuids. Consider only
        those submissions from enrollment, which are created before the specified date i.e. `delta_date`.
        """
        delta_date = datetime(2020, 1, 1, tzinfo=UTC).date()
        enrollment, expected_submissions, submission_uuid = self._create_enrollment_submission(
            submission_date,
            course_id=self.source_course.id,
            canceled_one_submission=True
        )

        submissions = helpers._get_submissions_to_autoscore_by_enrollment(enrollment, submission_uuid, delta_date)

        if submission_date < delta_date:
            self.assertEqual(expected_submissions, submissions)
        else:
            self.assertEqual([], submissions)

    def test_get_submissions_to_autoscore_by_enrollment_no_submissions(self):
        """
        Verify ORA submissions, which correspond to provided submission uuids, for an enrollment which do not have
        submission.
        """
        enrollment, _, _ = self._create_enrollment_submission(
            datetime(2019, 12, 30, tzinfo=UTC).date(),
            course_id=self.source_course.id,
            exclude_submissions=True
        )

        submissions = helpers._get_submissions_to_autoscore_by_enrollment(
            enrollment, [], datetime(2020, 1, 1, tzinfo=UTC).date()
        )

        self.assertEqual(submissions, [])

    def test_get_submissions_to_autoscore_by_enrollment_course_without_ora(self):
        """
        Verify ORA submissions, which correspond to provided submission uuids, for an enrollment of a course which do
        not have any ORA xblock.
        """
        course = CourseFactory.create(modulestore=self.store, emit_signals=False)
        enrollment, _, _ = self._create_enrollment_submission(
            datetime(2019, 12, 30, tzinfo=UTC).date(),
            course_id=course.id,
            exclude_submissions=True
        )
        enrollment = CourseEnrollmentFactory(course_id=course.id)
        AnonymousUserIdFactory(course_id=course.id, user=enrollment.user)

        submissions = helpers._get_submissions_to_autoscore_by_enrollment(
            enrollment, [], datetime(2020, 1, 1, tzinfo=UTC).date()
        )

        self.assertEqual(submissions, [])

    @mock.patch('openedx.features.assessment.helpers.select_options')
    def test_autoscore_ora_submission(self, mock_select_options):
        """
        Verify that ORA submission is auto scored by Philu bot which act as staff and assessment workflow status
        is marked to done.
        """
        mock_select_options.return_value = {'Ideas': 'Fair', 'Content': 'Fair'}, 4, 6
        block_usage_locator = BlockUsageLocator.from_string(unicode(self.all_ora_in_course[0].location))
        submission = SubmissionFactory(
            student_item__student_id='student_1',
            student_item__course_id=self.source_course.id.to_deprecated_string(),
            student_item__item_id=block_usage_locator
        )
        uuid = submission.uuid
        workflow_api.create_workflow(uuid, ["training", "peer", "self"])

        helpers.autoscore_ora_submission(submission)

        staff_assessment = Assessment.objects.filter(submission_uuid=uuid).order_by('-scored_at').first()
        assessment_workflow = AssessmentWorkflow.objects.filter(submission_uuid=uuid).order_by('-modified').first()
        score_by_bot = Score.objects.filter(submission=submission, reset=False).order_by('-created_at').first()

        self.assertIsNotNone(staff_assessment)
        self.assertIsNotNone(assessment_workflow)
        self.assertEqual(assessment_workflow.status, 'done')
        self.assertIsNotNone(score_by_bot)


@ddt
@pytest.mark.django_db
class AssessmentHelperTestCases(TestCase):
    """
    Assessment helper unit tests which do not require module store.
    """

    @mock.patch('openedx.features.assessment.helpers.log.info')
    def test_log_multiple_submissions_info_with_multiple_submissions(self, mock_log_info):
        """
        Verify logs for auto scoring of multiple submissions
        """
        submissions_to_autoscore = SubmissionFactory.create_batch(2)
        expected_logged_message = 'Autoscoring {count} submission(s)'.format(count=len(submissions_to_autoscore))

        helpers._log_multiple_submissions_info(submissions_to_autoscore, days_to_wait=mock.ANY, delta_date=mock.ANY)

        assert mock_log_info.called_with(expected_logged_message)

    @mock.patch('openedx.features.assessment.helpers.log.info')
    def test_log_multiple_submissions_info_with_no_submissions(self, mock_log_info):
        """
        Verify logs when there is no submission to autoscore
        """
        delta_date = datetime(2020, 1, 1).date()
        helpers._log_multiple_submissions_info(submissions_to_autoscore=[], days_to_wait=3, delta_date=delta_date)
        expected_logged_message = NO_PENDING_ORA.format(days=3, since_date=delta_date)
        assert mock_log_info.called_with(expected_logged_message)

    @mock.patch('openedx.features.assessment.helpers.autoscore_ora_submission')
    def test_autoscore_ora_submission_exists(self, mock_autoscore_ora_submission):
        """
        Verify that `autoscore_ora_submission` function is called with a valid submission object
        """
        submission = SubmissionFactory(
            student_item__student_id='student_1',
            student_item__course_id='course/id/123',
            student_item__item_id='item_id'
        )

        helpers.autoscore_ora(course_id=CourseKey.from_string('course/id/123'), usage_key='item_id', student={
            'anonymous_user_id': 'student_1'
        })

        mock_autoscore_ora_submission.assert_called_once_with(submission)

    @mock.patch('openedx.features.assessment.helpers.autoscore_ora_submission')
    def test_autoscore_ora_no_submission_found(self, mock_autoscore_ora_submission):
        """
        Verify that `autoscore_ora_submission` function is not called because submission object does not exist
        """
        helpers.autoscore_ora(course_id=CourseKey.from_string('course/id/123'), usage_key='item_id', student={
            'anonymous_user_id': 'student_1'
        })

        assert not mock_autoscore_ora_submission.called

    @unpack
    @data(
        (TWO_POINT_RUBRIC_DICTIONARY, {'Ideas': 'Fair', 'Content': 'Fair'}, 4, 4),
        (THREE_POINT_RUBRIC_DICTIONARY, {'Ideas': 'Fair', 'Content': 'Fair'}, 4, 6)
    )
    def test_select_options_with_two_point_rubric(self, rubric_dict, expected_options_selected,
                                                  expected_earned_points, expected_possible_points):
        """
        Validate rubric points calculation
        """
        actual_options_selected, actual_earned_points, actual_possible_points = helpers.select_options(rubric_dict)

        self.assertEqual(actual_options_selected, expected_options_selected)
        self.assertEqual(actual_earned_points, expected_earned_points)
        self.assertEqual(actual_possible_points, expected_possible_points)

    def test_get_philu_bot(self):
        """
        Verify that bot user is created if not already exists
        """
        helpers.get_philu_bot()

        self.assertTrue(User.objects.filter(username=PHILU_BOT_NAME).exists())

    @mock.patch('openedx.features.assessment.helpers.modulestore')
    def test_get_rubric_from_ora(self, mock_modulestore):
        """
        Test rubric for course
        """
        mock_get_item = mock_modulestore().get_item()
        mock_get_item.prompts.return_value = 'mock prompts'
        mock_get_item.rubric_criteria.return_value = 'mock criteria'
        expected_rubric_dict = {
            'prompts': mock_get_item.prompts,
            'criteria': mock_get_item.rubric_criteria
        }

        # Find the associated rubric for that course_id & item_id
        actual_rubric_dict = helpers.get_rubric_from_ora(mock.ANY)

        self.assertEqual(expected_rubric_dict, actual_rubric_dict)
