"""
Run these tests @ Devstack:
    paver test_system -t lms/djangoapps/progress/management/commands/tests/test_generate_progress_entries.py --fasttest
"""
from datetime import datetime
import uuid
import time

from django.db.models.signals import post_save

from capa.tests.response_xml_factory import StringResponseXMLFactory
from progress.management.commands import generate_progress_entries
from progress.models import StudentProgress, StudentProgressHistory
from progress.signals import handle_cmc_post_save_signal
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from api_manager.models import CourseModuleCompletion
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class GenerateProgressEntriesTests(ModuleStoreTestCase):
    """
    Test suite for progress generation script
    """

    def setUp(self):

        # Create a couple courses to work with
        self.course = CourseFactory.create(
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2015, 1, 16)
        )
        self.test_data = '<html>{}</html>'.format(str(uuid.uuid4()))

        chapter1 = ItemFactory.create(
            category="chapter",
            parent_location=self.course.location,
            data=self.test_data,
            due=datetime(2014, 5, 16, 14, 30),
            display_name="Overview"
        )

        chapter2 = ItemFactory.create(
            category="chapter",
            parent_location=self.course.location,
            data=self.test_data,
            due=datetime(2014, 5, 16, 14, 30),
            display_name="Overview"
        )
        self.problem = ItemFactory.create(
            parent_location=chapter1.location,
            category='problem',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name="homework problem 1",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Homework"}
        )
        self.problem2 = ItemFactory.create(
            parent_location=chapter2.location,
            category='problem',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name="homework problem 2",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Homework"}
        )
        self.problem3 = ItemFactory.create(
            parent_location=chapter2.location,
            category='problem',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name="lab problem 1",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Lab"}
        )

        # Create some users and enroll them
        self.users = [UserFactory.create(username="testuser" + str(__), profile='test') for __ in xrange(3)]
        for user in self.users:
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)
        # Turn off the signalling mechanism temporarily
        post_save.disconnect(receiver=handle_cmc_post_save_signal,
                             sender=CourseModuleCompletion, dispatch_uid='edxapp.api_manager.post_save_cms')
        self._generate_course_completion_test_entries()
        post_save.connect(receiver=handle_cmc_post_save_signal,
                          sender=CourseModuleCompletion, dispatch_uid='edxapp.api_manager.post_save_cms')

    def _generate_course_completion_test_entries(self):
        """
        Clears existing CourseModuleCompletion entries and creates 3 for each user
        """
        CourseModuleCompletion.objects.all().delete()
        for user in self.users:
            completion, created = CourseModuleCompletion.objects.get_or_create(user=user,
                                                                               course_id=self.course.id,
                                                                               content_id=unicode(self.problem.location),
                                                                               stage=None)

            completion, created = CourseModuleCompletion.objects.get_or_create(user=user,
                                                                               course_id=self.course.id,
                                                                               content_id=unicode(self.problem2.location),
                                                                               stage=None)

            completion, created = CourseModuleCompletion.objects.get_or_create(user=user,
                                                                               course_id=self.course.id,
                                                                               content_id=unicode(self.problem3.location),
                                                                               stage=None)

    def test_generate_progress_entries_command(self):
        """
        Test the progress entry generator
        """
        # Set up the command context
        course_ids = '{},bogus/course/id'.format(self.course.id)
        user_ids = '{}'.format(self.users[0].id)
        current_entries = StudentProgress.objects.all()
        self.assertEqual(len(current_entries), 0)
        current_entries = StudentProgressHistory.objects.all()
        self.assertEqual(len(current_entries), 0)

        # Run the command just for one user
        generate_progress_entries.Command().handle(user_ids=user_ids)

        # Confirm the progress has been properly updated
        current_entries = StudentProgress.objects.all()
        self.assertEqual(len(current_entries), 1)
        current_entries = StudentProgressHistory.objects.all()
        self.assertEqual(len(current_entries), 1)
        user0_entry = StudentProgress.objects.get(user=self.users[0])
        self.assertEqual(user0_entry.completions, 3)

        # Run the command across all users, but just for the specified course
        generate_progress_entries.Command().handle(course_ids=course_ids)

        # Confirm that the progress has been properly updated
        current_entries = StudentProgress.objects.all()
        self.assertEqual(len(current_entries), 3)
        current_entries = StudentProgressHistory.objects.all()
        self.assertEqual(len(current_entries), 3)
        user0_entry = StudentProgress.objects.get(user=self.users[0])
        self.assertEqual(user0_entry.completions, 3)
        user1_entry = StudentProgress.objects.get(user=self.users[1])
        self.assertEqual(user1_entry.completions, 3)
        user2_entry = StudentProgress.objects.get(user=self.users[2])
        self.assertEqual(user2_entry.completions, 3)

    def test_progress_history(self):
        """
        Test the progress, and history
        """
        # Clear enteries
        StudentProgress.objects.all().delete()
        StudentProgressHistory.objects.all().delete()
        self._generate_course_completion_test_entries()

        #let single bindings to complete their work
        time.sleep(2)
        current_entries = StudentProgress.objects.all()
        self.assertEqual(len(current_entries), 3)
        current_entries = StudentProgressHistory.objects.all()
        self.assertEqual(len(current_entries), 9)
        user0_entry = StudentProgress.objects.get(user=self.users[0])
        self.assertEqual(user0_entry.completions, 3)
