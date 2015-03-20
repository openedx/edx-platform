"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/management/commands/tests/test_migrate_orgdata.py]
"""
from datetime import datetime
import uuid

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.test.utils import override_settings

from api_manager import models as api_models
from progress.models import CourseModuleCompletion
from api_manager.management.commands import migrate_courseids
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, mixed_store_config
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)
from django.db import connection

@override_settings(MODULESTORE=MODULESTORE_CONFIG)
class MigrateCourseIdsTests(ModuleStoreTestCase):
    """
    Test suite for data migration script
    """

    def setUp(self):
        super(MigrateCourseIdsTests, self).setUp()
        self.course = CourseFactory.create(
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2020, 1, 16)
        )
        self.test_data = '<html>{}</html>'.format(str(uuid.uuid4()))

        self.chapter = ItemFactory.create(
            category="chapter",
            parent_location=self.course.location,
            data=self.test_data,
            due=datetime(2014, 5, 16, 14, 30),
            display_name="Overview"
        )

        self.old_style_course_id = self.course.id.to_deprecated_string()
        self.new_style_course_id = unicode(self.course.id)
        self.old_style_content_id = self.chapter.location.to_deprecated_string()
        self.new_style_content_id = unicode(self.chapter.location)

        self.course2 = CourseFactory.create(
            org='TEST',
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2020, 1, 16)
        )
        self.chapter2 = ItemFactory.create(
            category="chapter",
            parent_location=self.course2.location,
            data=self.test_data,
            due=datetime(2014, 5, 16, 14, 30),
            display_name="Overview"
        )

        self.new_style_course_id2 = unicode(self.course2.id)
        self.new_style_content_id2 = unicode(self.chapter2.location)


    def test_migrate_courseids(self):
        """
        Test the data migration
        """
        # Set up the data to be migrated
        user = User.objects.create(email='testuser@edx.org', username='testuser', password='testpassword', is_active=True)
        group = Group.objects.create(name='Test Group')
        group_profile = api_models.GroupProfile.objects.create(group=group)
        course_group = api_models.CourseGroupRelationship.objects.create(course_id=self.old_style_course_id, group=group)
        course_content_group = api_models.CourseContentGroupRelationship.objects.create(course_id=self.old_style_course_id, content_id=self.old_style_content_id, group_profile=group_profile)
        course_module_completion = CourseModuleCompletion.objects.create(user=user, course_id=self.old_style_course_id, content_id=self.old_style_content_id)

        user2 = User.objects.create(email='testuser2@edx.org', username='testuser2', password='testpassword2', is_active=True)
        group2 = Group.objects.create(name='Test Group2')
        group_profile2 = api_models.GroupProfile.objects.create(group=group2)
        course_group2 = api_models.CourseGroupRelationship.objects.create(course_id=self.new_style_course_id2, group=group2)
        course_content_group2 = api_models.CourseContentGroupRelationship.objects.create(course_id=self.new_style_course_id2, content_id=self.new_style_content_id2, group_profile=group_profile2)
        course_module_completion2 = CourseModuleCompletion.objects.create(user=user2, course_id=self.new_style_course_id2, content_id=self.new_style_content_id2)


        # Run the data migration
        migrate_courseids.Command().handle()


        # Confirm that the data has been properly migrated
        updated_course_group = api_models.CourseGroupRelationship.objects.get(id=course_group.id)
        self.assertEqual(updated_course_group.course_id, self.new_style_course_id)
        updated_course_group = api_models.CourseGroupRelationship.objects.get(id=course_group2.id)
        self.assertEqual(updated_course_group.course_id, self.new_style_course_id2)
        print "Course Group Data Migration Passed"

        updated_course_content_group = api_models.CourseContentGroupRelationship.objects.get(id=course_content_group.id)
        self.assertEqual(updated_course_content_group.course_id, self.new_style_course_id)
        self.assertEqual(updated_course_content_group.content_id, self.new_style_content_id)
        updated_course_content_group = api_models.CourseContentGroupRelationship.objects.get(id=course_content_group2.id)
        self.assertEqual(updated_course_content_group.course_id, self.new_style_course_id2)
        self.assertEqual(updated_course_content_group.content_id, self.new_style_content_id2)
        print "Course Content Group Data Migration Passed"

        updated_course_module_completion = CourseModuleCompletion.objects.get(id=course_module_completion.id)
        self.assertEqual(updated_course_module_completion.course_id, self.new_style_course_id)
        self.assertEqual(updated_course_module_completion.content_id, self.new_style_content_id)
        updated_course_module_completion = CourseModuleCompletion.objects.get(id=course_module_completion2.id)
        self.assertEqual(updated_course_module_completion.course_id, self.new_style_course_id2)
        self.assertEqual(updated_course_module_completion.content_id, self.new_style_content_id2)
        print "Course Module Completion Data Migration Passed"
