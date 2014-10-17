"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/management/commands/tests/test_migrate_orgdata.py]
"""
from datetime import datetime
import uuid

from django.contrib.auth.models import Group, User

from api_manager import models as api_models
from api_manager.management.commands import migrate_courseids_v2
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class MigrateCourseIdsTests(ModuleStoreTestCase):
    """
    Test suite for data migration script
    """

    def setUp(self):

        self.bad_style_course_id = "slashes:old+style+id"
        self.good_style_course_id = "old/style/id"
        self.bad_style_content_id = "location:old+style+id+chapter+1234567890"
        self.good_style_content_id = "i4x://old/style/chapter/1234567890"

        self.bad_style_course_id2 = "course-v1:old2+style2+id2"
        self.good_style_course_id2 = "old2/style2/id2"
        self.bad_style_content_id2 = "location:old2+style2+id2+chapter2+1234567890"
        self.good_style_content_id2 = "i4x://old2/style2/chapter2/1234567890"


    def test_migrate_courseids_v2(self):
        """
        Test the data migration
        """
        # Set up the data to be migrated
        user = User.objects.create(email='testuser@edx.org', username='testuser', password='testpassword', is_active=True)
        group = Group.objects.create(name='Test Group')
        group_profile = api_models.GroupProfile.objects.create(group=group)
        course_group = api_models.CourseGroupRelationship.objects.create(course_id=self.bad_style_course_id, group=group)
        course_content_group = api_models.CourseContentGroupRelationship.objects.create(course_id=self.bad_style_course_id, content_id=self.bad_style_content_id, group_profile=group_profile)
        course_module_completion = api_models.CourseModuleCompletion.objects.create(user=user, course_id=self.bad_style_course_id, content_id=self.bad_style_content_id)

        user2 = User.objects.create(email='testuser2@edx.org', username='testuser2', password='testpassword2', is_active=True)
        group2 = Group.objects.create(name='Test Group2')
        group_profile2 = api_models.GroupProfile.objects.create(group=group2)
        course_group2 = api_models.CourseGroupRelationship.objects.create(course_id=self.bad_style_course_id2, group=group2)
        course_content_group2 = api_models.CourseContentGroupRelationship.objects.create(course_id=self.bad_style_course_id2, content_id=self.bad_style_content_id2, group_profile=group_profile2)
        course_module_completion2 = api_models.CourseModuleCompletion.objects.create(user=user2, course_id=self.bad_style_course_id2, content_id=self.bad_style_content_id2, stage=self.bad_style_content_id2)


        # Run the data migration
        migrate_courseids_v2.Command().handle()


        # Confirm that the data has been properly migrated
        updated_course_group = api_models.CourseGroupRelationship.objects.get(id=course_group.id)
        self.assertEqual(updated_course_group.course_id, self.good_style_course_id)
        updated_course_group = api_models.CourseGroupRelationship.objects.get(id=course_group2.id)
        self.assertEqual(updated_course_group.course_id, self.good_style_course_id2)
        print "Course Group Data Migration Passed"

        updated_course_content_group = api_models.CourseContentGroupRelationship.objects.get(id=course_content_group.id)
        self.assertEqual(updated_course_content_group.course_id, self.good_style_course_id)
        self.assertEqual(updated_course_content_group.content_id, self.good_style_content_id)
        updated_course_content_group = api_models.CourseContentGroupRelationship.objects.get(id=course_content_group2.id)
        self.assertEqual(updated_course_content_group.course_id, self.good_style_course_id2)
        self.assertEqual(updated_course_content_group.content_id, self.good_style_content_id2)
        print "Course Content Group Data Migration Passed"

        updated_course_module_completion = api_models.CourseModuleCompletion.objects.get(id=course_module_completion.id)
        self.assertEqual(updated_course_module_completion.course_id, self.good_style_course_id)
        self.assertEqual(updated_course_module_completion.content_id, self.good_style_content_id)
        updated_course_module_completion = api_models.CourseModuleCompletion.objects.get(id=course_module_completion2.id)
        self.assertEqual(updated_course_module_completion.course_id, self.good_style_course_id2)
        self.assertEqual(updated_course_module_completion.content_id, self.good_style_content_id2)
        self.assertEqual(updated_course_module_completion.stage, self.good_style_content_id2)
        print "Course Module Completion Data Migration Passed"
