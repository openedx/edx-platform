""" Test Assessment Helpers. """
import time
from datetime import datetime, timedelta

import mock
from ddt import data, ddt, unpack
from django.contrib.auth.models import User
from django.utils.timezone import now
from opaque_keys.edx.locator import BlockUsageLocator
from openassessment.assessment.models import Assessment, AssessmentPart
from pytz import UTC

from openedx.features.assessment import helpers
from openedx.features.assessment.tests.factories import StudentItemFactory, SubmissionFactory
from student.tests.factories import AnonymousUserIdFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from .constants import (
    COURSE_CHILD_STRUCTURE,
    PHILU_BOT_NAME,
    THREE_POINT_RUBRIC_DICTIONARY,
    TWO_POINT_RUBRIC_DICTIONARY
)

FOUR_DAYS_AGO = now() - timedelta(days=4)


@ddt
class AssessmentHelperTestCases(ModuleStoreTestCase):
    """ Assessment Helper unit tests """

    def create_course_chapter_with_specific_xblocks(self, course):
        """ Create course chapter with specific xblocks. """
        for unit in self.xblock_types:
            self.create_course_children(self.store, course, 'chapter', unit)

    def create_course_children(self, store, parent, category, unit):
        """ Create course children recursively as an input for test cases. """
        child_object = ItemFactory.create(
            parent_location=parent.location,
            category=category,
            display_name=u"{} {}".format(category, time.clock()),
            modulestore=store,
            publish_item=True,
        )

        if category not in COURSE_CHILD_STRUCTURE:
            return

        category = unit if category == 'vertical' else COURSE_CHILD_STRUCTURE[category]
        self.create_course_children(store, child_object, category, unit)

    def setUp(self):
        super(AssessmentHelperTestCases, self).setUp()

        self.xblock_types = ['openassessment', ]

        self.source_course = CourseFactory.create(
            modulestore=self.store,
            start=datetime(2019, 9, 1, tzinfo=UTC),
            emit_signals=False)
        self.create_course_chapter_with_specific_xblocks(self.source_course)

        self.all_ora_in_course = modulestore().get_items(
            self.source_course.id,
            qualifiers={'category': 'openassessment'}
        )

        self.block_usage_locator = BlockUsageLocator.from_string(unicode(self.all_ora_in_course[0].location))

    @mock.patch('openedx.features.assessment.helpers.log.info')
    def test_log_multiple_submissions_info_with_multiple_submissions(self, mock_log_info):
        submissions = SubmissionFactory.create_batch(2)
        submission_ids = map(str, [submission.id for submission in submissions])

        expected_logged_message = 'Multiple submissions found having ids {ids} in can_auto_score_ora'.format(
            ids=','.join(submission_ids))

        helpers._log_multiple_submissions_info(submissions)
        assert mock_log_info.called_with(expected_logged_message)

    @mock.patch('openedx.features.assessment.helpers.log.info')
    def test_log_multiple_submissions_info_with_no_submissions(self, mock_log_info):
        submissions = []
        helpers._log_multiple_submissions_info(submissions)
        assert mock_log_info.not_called

    @mock.patch('openedx.features.assessment.helpers.log.info')
    @mock.patch('openedx.features.assessment.helpers.reset_score')
    @mock.patch('openedx.features.assessment.helpers.set_score')
    @mock.patch('openedx.features.assessment.helpers.select_options')
    def test_autoscore_ora_successfully(self, mock_select_options, mock_set_score,
                                        mock_reset_score, mock_log_info):
        """ Mock test score methods when there is valid submission exists """

        mock_select_options.return_value = {'Ideas': 'Fair', 'Content': 'Fair'}, 4, 6

        anonymous_user = AnonymousUserIdFactory(user=self.user, course_id=self.source_course.id)

        # create submission item
        student_item = StudentItemFactory(
            student_id=anonymous_user.anonymous_user_id,
            course_id=self.source_course.id,
            item_id=self.block_usage_locator
        )
        submission = SubmissionFactory(
            student_item=student_item,
            created_at=FOUR_DAYS_AGO
        )
        student = {
            'anonymous_user_id': anonymous_user.anonymous_user_id
        }
        submission_uuid = str(submission.uuid)
        helpers.autoscore_ora(self.source_course.id, unicode(self.block_usage_locator), student)

        self.assertTrue(Assessment.objects.all().exists())
        self.assertTrue(AssessmentPart.objects.all().exists())

        assert mock_set_score.called_with(submission_uuid, mock_select_options.return_value[1],
                                          mock_select_options.return_value[2])
        assert mock_reset_score.called_with(anonymous_user.anonymous_user_id,
                                            self.source_course.id.to_deprecated_string(),
                                            unicode(self.block_usage_locator))
        assert mock_log_info.called_once

    @mock.patch('openedx.features.assessment.helpers.log.info')
    @mock.patch('openedx.features.assessment.helpers.log.warn')
    @mock.patch('openedx.features.assessment.helpers.reset_score')
    @mock.patch('openedx.features.assessment.helpers.set_score')
    def test_autoscore_ora_with_no_submission(self, mock_set_score, mock_reset_score, mock_log_warn, mock_log_info):
        """ Test auto score without any ora submissions """

        anonymous_user = AnonymousUserIdFactory(user=self.user, course_id=self.source_course.id)

        student = {
            'anonymous_user_id': anonymous_user.anonymous_user_id
        }
        helpers.autoscore_ora(self.source_course.id, unicode(self.block_usage_locator), student)

        self.assertEqual(Assessment.objects.all().count(), 0)
        self.assertEqual(AssessmentPart.objects.all().count(), 0)
        assert mock_set_score.not_called
        assert mock_reset_score.not_called
        assert mock_log_warn.called_once
        assert mock_log_info.not_called

    @data(
        (TWO_POINT_RUBRIC_DICTIONARY, {'Ideas': 'Fair', 'Content': 'Fair'}, 4, 4),
        (THREE_POINT_RUBRIC_DICTIONARY, {'Ideas': 'Fair', 'Content': 'Fair'}, 4, 6)
    )
    @unpack
    def test_select_options_with_two_point_rubric(self, rubric_dict, expected_options_selected,
                                                  expected_earned_points, expected_possible_points):
        """ Validate rubric points calculation """

        actual_options_selected, actual_earned_points, actual_possible_points = helpers.select_options(rubric_dict)

        self.assertEqual(actual_options_selected, expected_options_selected)
        self.assertEqual(actual_earned_points, expected_earned_points)
        self.assertEqual(actual_possible_points, expected_possible_points)

    def test_get_philu_bot(self):
        """ Verify that bot user is created if not already exists """
        helpers.get_philu_bot()
        self.assertTrue(User.objects.filter(username=PHILU_BOT_NAME).exists())

    @mock.patch('openedx.features.assessment.helpers.modulestore')
    def test_get_rubric_for_course(self, mock_modulestore):
        """ Test rubric for course """
        mock_get_item = mock_modulestore().get_item()
        mock_get_item.prompts.return_value = 'mock prompts'
        mock_get_item.rubric_criteria.return_value = 'mock criteria'
        expected_rubric_dict = {
            'prompts': mock_get_item.prompts,
            'criteria': mock_get_item.rubric_criteria
        }

        # Find the associated rubric for that course_id & item_id
        actual_rubric_dict = helpers.get_rubric_for_course(self.source_course.id,
                                                           unicode(self.block_usage_locator))

        self.assertEqual(expected_rubric_dict, actual_rubric_dict)
