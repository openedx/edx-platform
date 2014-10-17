"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/management/commands/tests/test_migrate_orgdata.py]
"""
from datetime import datetime
import uuid

from django.contrib.auth.models import User

from gradebook import models as gradebook_models
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from gradebook.management.commands import migrate_gradebook_courseids_v2
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

    def test_migrate_courseids(self):
        """
        Test the data migration
        """
        # Set up the data to be migrated
        user = User.objects.create(email='testuser@edx.org', username='testuser', password='testpassword', is_active=True)
        gradebook_entry = gradebook_models.StudentGradebook.objects.create(user=user, course_id=self.bad_style_course_id, grade=0.85, proforma_grade=0.74)

        user2 = User.objects.create(email='testuser2@edx.org', username='testuser2', password='testpassword2', is_active=True)
        gradebook_entry2 = gradebook_models.StudentGradebook.objects.create(user=user2, course_id=self.bad_style_course_id2, grade=0.95, proforma_grade=0.64)


        # Run the data migration
        migrate_gradebook_courseids_v2.Command().handle()


        # Confirm that the data has been properly migrated
        updated_gradebook_entries = gradebook_models.StudentGradebook.objects.get(id=gradebook_entry.id)
        updated_gradebook_entry = gradebook_models.StudentGradebook.objects.get(id=gradebook_entry2.id)
        self.assertEqual(unicode(updated_gradebook_entry.course_id), self.good_style_course_id2)
        print "Student Gradebook Data Migration Passed"

        updated_history_entries = gradebook_models.StudentGradebookHistory.objects.filter(user=user.id)
        for entry in updated_history_entries:
            self.assertEqual(unicode(entry.course_id), self.good_style_course_id)
        updated_history_entries = gradebook_models.StudentGradebookHistory.objects.filter(user=user2.id)
        for entry in updated_history_entries:
            self.assertEqual(unicode(entry.course_id), self.good_style_course_id2)
        print "Student Gradebook History Data Migration Passed"
