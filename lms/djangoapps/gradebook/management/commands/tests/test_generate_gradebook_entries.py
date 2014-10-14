"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/management/commands/tests/test_migrate_orgdata.py]
"""
from datetime import datetime
from mock import MagicMock
import uuid

from django.conf import settings

from capa.tests.response_xml_factory import StringResponseXMLFactory
from courseware import module_render
from courseware.model_data import FieldDataCache
from gradebook.management.commands import generate_gradebook_entries
from gradebook.models import StudentGradebook, StudentGradebookHistory
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class GenerateGradebookEntriesTests(ModuleStoreTestCase):
    """
    Test suite for grade generation script
    """

    def setUp(self):

        # Turn off the signalling mechanism temporarily
        settings._wrapped.default_settings.FEATURES['SIGNAL_ON_SCORE_CHANGED'] = False

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
        self.problem4 = ItemFactory.create(
            parent_location=chapter2.location,
            category='problem',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name="midterm problem 2",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Midterm Exam"}
        )
        self.problem5 = ItemFactory.create(
            parent_location=chapter2.location,
            category='problem',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name="final problem 2",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Final Exam"}
        )

        # Create some users and enroll them
        self.users = [UserFactory.create(username="testuser" + str(__), profile='test') for __ in xrange(3)]
        for user in self.users:
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)

            grade = 0.15 * user.id
            module = self.get_module_for_user(user, self.course, self.problem)
            grade_dict = {'value': grade, 'max_value': 1, 'user_id': user.id}
            module.system.publish(module, 'grade', grade_dict)

            grade = 0.20 * user.id
            module = self.get_module_for_user(user, self.course, self.problem2)
            grade_dict = {'value': grade, 'max_value': 1, 'user_id': user.id}
            module.system.publish(module, 'grade', grade_dict)

            grade = 0.25 * user.id
            module = self.get_module_for_user(user, self.course, self.problem3)
            grade_dict = {'value': grade, 'max_value': 1, 'user_id': user.id}
            module.system.publish(module, 'grade', grade_dict)

            grade = 0.30 * user.id
            module = self.get_module_for_user(user, self.course, self.problem4)
            grade_dict = {'value': grade, 'max_value': 1, 'user_id': user.id}
            module.system.publish(module, 'grade', grade_dict)

            grade = 0.33 * user.id
            module = self.get_module_for_user(user, self.course, self.problem5)
            grade_dict = {'value': grade, 'max_value': 1, 'user_id': user.id}
            module.system.publish(module, 'grade', grade_dict)

    def get_module_for_user(self, user, course, problem):
        """Helper function to get useful module at self.location in self.course_id for user"""
        mock_request = MagicMock()
        mock_request.user = user
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            course.id, user, course, depth=2)

        return module_render.get_module(  # pylint: disable=protected-access
            user,
            mock_request,
            problem.location,
            field_data_cache,
            course.id
        )._xmodule

    def test_generate_gradebook_entries(self):
        """
        Test the gradebook entry generator
        """
        # Set up the command context
        course_ids = '{},bogus/course/id'.format(self.course.id)
        user_ids = '{}'.format(self.users[0].id)
        current_entries = StudentGradebook.objects.all()
        self.assertEqual(len(current_entries), 0)
        current_entries = StudentGradebookHistory.objects.all()
        self.assertEqual(len(current_entries), 0)

        # Run the command just for one user
        generate_gradebook_entries.Command().handle(user_ids=user_ids)

        # Confirm the gradebook has been properly updated
        current_entries = StudentGradebook.objects.all()
        self.assertEqual(len(current_entries), 1)
        current_entries = StudentGradebookHistory.objects.all()
        self.assertEqual(len(current_entries), 1)
        user0_entry = StudentGradebook.objects.get(user=self.users[0])
        self.assertEqual(user0_entry.grade, 0.24)

        # Enable the signalling mechanism
        settings._wrapped.default_settings.FEATURES['SIGNAL_ON_SCORE_CHANGED'] = True

        # Change the score of the final exam for that user
        grade = 0.99
        module = self.get_module_for_user(self.users[0], self.course, self.problem5)
        grade_dict = {'value': grade, 'max_value': 1, 'user_id': self.users[0].id}
        module.system.publish(module, 'grade', grade_dict)

        # Confirm the gradebook has been properly updated
        current_entries = StudentGradebook.objects.all()
        self.assertEqual(len(current_entries), 1)
        current_entries = StudentGradebookHistory.objects.all()
        self.assertEqual(len(current_entries), 2)
        user0_entry = StudentGradebook.objects.get(user=self.users[0])
        self.assertEqual(user0_entry.grade, 0.50)

        # Run the command across all users, but just for the specified course
        generate_gradebook_entries.Command().handle(course_ids=course_ids)

        # Confirm that the gradebook has been properly updated
        current_entries = StudentGradebook.objects.all()
        self.assertEqual(len(current_entries), 3)
        current_entries = StudentGradebookHistory.objects.all()
        self.assertEqual(len(current_entries), 4)
        user0_entry = StudentGradebook.objects.get(user=self.users[0])
        self.assertEqual(user0_entry.grade, 0.50)
        user1_entry = StudentGradebook.objects.get(user=self.users[1])
        self.assertEqual(user1_entry.grade, 0.48)
        user2_entry = StudentGradebook.objects.get(user=self.users[2])
        self.assertEqual(user2_entry.grade, 0.72)
