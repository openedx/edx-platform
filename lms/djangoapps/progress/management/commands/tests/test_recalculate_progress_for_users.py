"""
Tests for recalculate_progress_for_users.py
"""
from datetime import datetime
import uuid

from django.conf import settings
from django.test.utils import override_settings
from django.db.models.signals import post_save

from capa.tests.response_xml_factory import StringResponseXMLFactory
from progress.management.commands import recalculate_progress_for_users
from progress.models import StudentProgress, StudentProgressHistory, CourseModuleCompletion
from progress.signals import handle_cmc_post_save_signal
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, mixed_store_config
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


@override_settings(MODULESTORE=MODULESTORE_CONFIG)
class RecalculateProgressEntriesTests(ModuleStoreTestCase):
    """
    Test suite for progress recalculation script
    """

    def setUp(self):
        super(RecalculateProgressEntriesTests, self).setUp()

        self.course = CourseFactory.create(
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2020, 1, 16)
        )
        self.test_data = '<html>{}</html>'.format(str(uuid.uuid4()))

        chapter1 = ItemFactory.create(
            category="chapter",
            parent_location=self.course.location,
            data=self.test_data,
            due=datetime(2014, 5, 16, 14, 30),
            display_name="Overview"
        )

        sub_section1 = ItemFactory.create(
            category="sequential",
            parent_location=chapter1.location,
            display_name="Sequential 1",
        )

        vertical1 = ItemFactory.create(
            category="vertical",
            parent_location=sub_section1.location,
            display_name="Vertical 1"
        )

        chapter2 = ItemFactory.create(
            category="chapter",
            parent_location=self.course.location,
            data=self.test_data,
            due=datetime(2014, 5, 16, 14, 30),
            display_name="Overview"
        )

        sub_section2 = ItemFactory.create(
            category="sequential",
            parent_location=chapter2.location,
            display_name="Sequential 2",
        )

        vertical2 = ItemFactory.create(
            category="vertical",
            parent_location=sub_section2.location,
            display_name="Vertical 2"
        )

        self.problem = ItemFactory.create(
            parent_location=vertical1.location,
            category='problem',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name="homework problem 1",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Homework"}
        )
        self.problem2 = ItemFactory.create(
            parent_location=vertical2.location,
            category='problem',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name="homework problem 2",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Homework"}
        )
        self.problem3 = ItemFactory.create(
            parent_location=vertical2.location,
            category='problem',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name="lab problem 1",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Lab"}
        )
        self.problem4 = ItemFactory.create(
            parent_location=vertical2.location,
            category='problem',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name="lab problem 2",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Lab"}
        )
        self.non_vertical_problem = ItemFactory.create(
            parent_location=chapter1.location,
            category='problem',
            display_name="non vertical problem",
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
        for idx, user in enumerate(self.users):
            if idx % 2 == 0:
                StudentProgress.objects.get_or_create(
                    user_id=user.id, course_id=self.course.id, completions=0
                )
            CourseModuleCompletion.objects.get_or_create(user=user,
                                                         course_id=self.course.id,
                                                         content_id=unicode(self.problem.location),
                                                         stage=None)

            CourseModuleCompletion.objects.get_or_create(user=user,
                                                         course_id=self.course.id,
                                                         content_id=unicode(self.problem2.location),
                                                         stage=None)

            CourseModuleCompletion.objects.get_or_create(user=user,
                                                         course_id=self.course.id,
                                                         content_id=unicode(self.problem3.location),
                                                         stage=None)
            CourseModuleCompletion.objects.get_or_create(user=user,
                                                         course_id=self.course.id,
                                                         content_id=unicode(self.non_vertical_problem.location),
                                                         stage=None)

    def test_generate_progress_entries_command(self):
        """
        Test the progress entry generator
        """
        # Set up the command context
        course_ids = '{},bogus/course/id'.format(self.course.id)
        user_ids = '{}'.format(self.users[0].id)
        current_entries = StudentProgress.objects.all()
        self.assertEqual(len(current_entries), 2)
        current_entries = StudentProgressHistory.objects.all()
        self.assertEqual(len(current_entries), 2)

        # Run the command just for one user
        recalculate_progress_for_users.Command().handle(user_ids=user_ids)

        # Confirm the progress has been properly updated
        current_entries = StudentProgress.objects.all()
        self.assertEqual(len(current_entries), 2)
        current_entries = StudentProgressHistory.objects.all()
        self.assertEqual(len(current_entries), 3)
        user0_entry = StudentProgress.objects.get(user=self.users[0])
        self.assertEqual(user0_entry.completions, 3)

        # Run the command across all users, but just for the specified course
        recalculate_progress_for_users.Command().handle(course_ids=course_ids)

        # The first user will be skipped this next time around because they already have a progress record
        # and their completions have not changed
        user0_entry = StudentProgress.objects.get(user=self.users[0])
        self.assertEqual(user0_entry.completions, 3)

        # Confirm that the progress has been properly updated
        current_entries = StudentProgress.objects.all()
        self.assertEqual(len(current_entries), 2)
        current_entries = StudentProgressHistory.objects.all()
        self.assertEqual(len(current_entries), 4)

        # second user has no entry in StudentProgress so they should b skipped
        user1_entry = StudentProgress.objects.filter(user=self.users[1])
        self.assertEqual(len(user1_entry), 0)

        # third user should have their progress updated
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

        current_entries = StudentProgress.objects.all()
        self.assertEqual(len(current_entries), 3)
        current_entries = StudentProgressHistory.objects.all()
        # StudentProgressHistory should have 11 entries
        # 9 entries for progress history of 3 users each with 3 completions
        # and 2 entries for initial progress creation of 2 users
        self.assertEqual(len(current_entries), 11)
        user0_entry = StudentProgress.objects.get(user=self.users[0])
        self.assertEqual(user0_entry.completions, 3)
