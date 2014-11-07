"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/management/commands/tests/test_migrate_orgdata.py]
"""
from datetime import datetime
import uuid

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.test.utils import override_settings

from progress.models import CourseModuleCompletion
from api_manager.management.commands import migrate_stage_prefix
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from django.db import connection

@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class MigrateCourseIdsTests(TestCase):
    """
    Test suite for data migration script
    """

    def setUp(self):

        self.good_style_course_id = "old/style/id"
        self.good_style_content_id = "i4x://old/style/chapter/1234567890"
        self.bad_style_stage = 'i4x://evaluation'
        self.good_style_stage = 'evaluation'

        self.good_style_course_id2 = "old2/style2/id2"
        self.good_style_content_id2 = "i4x://old2/style2/chapter2/1234567890"
        self.bad_style_stage2 = 'i4x://upload'
        self.good_style_stage2 = 'upload'

    def test_migrate_stage_prefix(self):
        """
        Test the data migration
        """
        # Set up the data to be migrated
        user = User.objects.create(email='testuser@edx.org', username='testuser', password='testpassword', is_active=True)
        course_module_completion = CourseModuleCompletion.objects.create(user=user, course_id=self.good_style_course_id, content_id=self.good_style_content_id, stage=self.bad_style_stage)

        user2 = User.objects.create(email='testuser2@edx.org', username='testuser2', password='testpassword2', is_active=True)
        course_module_completion2 = CourseModuleCompletion.objects.create(user=user2, course_id=self.good_style_course_id2, content_id=self.good_style_content_id2, stage=self.bad_style_stage2)


        # Run the data migration
        migrate_stage_prefix.Command().handle()


        updated_course_module_completion = CourseModuleCompletion.objects.get(id=course_module_completion.id)
        self.assertEqual(updated_course_module_completion.stage, self.good_style_stage)

        updated_course_module_completion = CourseModuleCompletion.objects.get(id=course_module_completion2.id)
        self.assertEqual(updated_course_module_completion.stage, self.good_style_stage2)
        print "Course Module Completion Data Migration Passed"
