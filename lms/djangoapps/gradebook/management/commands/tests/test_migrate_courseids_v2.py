"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/management/commands/tests/test_migrate_orgdata.py]
"""
from datetime import datetime
import uuid

from django.contrib.auth.models import User

from gradebook import models as gradebook_models
from gradebook.management.commands import migrate_courseids_v2
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class MigrateCourseIdsTests(ModuleStoreTestCase):
    """
    Test suite for data migration script
    """

    def setUp(self):

        self.course = CourseFactory.create(
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2015, 1, 16)
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
            end=datetime(2015, 1, 16)
        )
        self.chapter2 = ItemFactory.create(
            category="chapter",
            parent_location=self.course2.location,
            data=self.test_data,
            due=datetime(2014, 5, 16, 14, 30),
            display_name="Overview"
        )

        self.old_style_course_id2 = self.course2.id.to_deprecated_string()
        self.new_style_course_id2 = unicode(self.course2.id)
        self.old_style_content_id2 = self.chapter2.location.to_deprecated_string()
        self.new_style_content_id2 = unicode(self.chapter2.location)


    def test_migrate_courseids(self):
        """
        Test the data migration
        """
        # Set up the data to be migrated
        user = User.objects.create(email='testuser@edx.org', username='testuser', password='testpassword', is_active=True)
        gradebook_entry = gradebook_models.StudentGradebook.objects.create(user=user, course_id=self.new_style_course_id, grade=0.85, proforma_grade=0.74)

        user2 = User.objects.create(email='testuser2@edx.org', username='testuser2', password='testpassword2', is_active=True)
        gradebook_entry2 = gradebook_models.StudentGradebook.objects.create(user=user2, course_id=self.new_style_course_id2, grade=0.95, proforma_grade=0.64)


        # Run the data migration
        migrate_courseids_v2.Command().handle()


        # Confirm that the data has been properly migrated
        updated_gradebook_entries = gradebook_models.StudentGradebook.objects.get(id=gradebook_entry.id)
        updated_gradebook_entry = gradebook_models.StudentGradebook.objects.get(id=gradebook_entry2.id)
        self.assertEqual(unicode(updated_gradebook_entry.course_id), self.old_style_course_id2)
        print "Student Gradebook Data Migration Passed"

        updated_history_entries = gradebook_models.StudentGradebookHistory.objects.filter(user=user.id)
        for entry in updated_history_entries:
            self.assertEqual(unicode(entry.course_id), self.old_style_course_id)
        updated_history_entries = gradebook_models.StudentGradebookHistory.objects.filter(user=user2.id)
        for entry in updated_history_entries:
            self.assertEqual(unicode(entry.course_id), self.old_style_course_id2)
        print "Student Gradebook History Data Migration Passed"
