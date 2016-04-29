"""
Tests to support bulk_delete_courses_with_reference_data django management command
"""
import mock
import pytz
from datetime import datetime, timedelta
from freezegun import freeze_time
from mock import PropertyMock

from django.conf import settings
from django.core.management import call_command
from django.test.utils import override_settings

from api_manager.models import CourseGroupRelationship
from gradebook.models import StudentGradebook
from progress.models import StudentProgress, CourseModuleCompletion
from student.models import CourseEnrollment, CourseAccessRole
from openedx.core.djangoapps.content.course_metadata.models import CourseAggregatedMetaData
from openedx.core.djangoapps.content.course_structures.models import CourseStructure
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from courseware.models import StudentModule
from student.tests.factories import UserFactory, GroupFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, mixed_store_config
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.django import modulestore
from xmodule.course_module import CourseDescriptor

MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


@override_settings(MODULESTORE=MODULESTORE_CONFIG)
class BulkCourseDeleteTests(ModuleStoreTestCase):
    """
    Test suite for bulk course delete script
    """
    YESNO_PATCH_LOCATION = 'api_manager.management.commands.bulk_delete_courses_with_reference_data.query_yes_no'

    def setUp(self):
        super(BulkCourseDeleteTests, self).setUp()

    @staticmethod
    def create_course():
        """
        Creates a course with just one chapter inside it
        """
        course = CourseFactory.create()
        ItemFactory.create(
            category="chapter",
            parent_location=course.location,
            display_name="Overview"
        )
        return course

    @staticmethod
    def create_course_reference_data(course_key):
        """
        Populates DB with test data
        """
        user = UserFactory()
        group = GroupFactory()
        CourseGroupRelationship(course_id=course_key, group=group).save()
        StudentGradebook(
            user=user,
            course_id=course_key,
            grade=0.9,
            proforma_grade=0.91,
            progress_summary='test',
            grade_summary='test',
            grading_policy='test',
        ).save()
        StudentProgress(user=user, course_id=course_key, completions=1).save()
        CourseModuleCompletion(user=user, course_id=course_key, content_id='test', stage='test').save()
        CourseEnrollment(user=user, course_id=course_key).save()
        CourseAccessRole(user=user, course_id=course_key, org='test', role='TA').save()
        handouts_usage_key = course_key.make_usage_key('course_info', 'handouts')
        StudentModule(student=user, course_id=course_key, module_state_key=handouts_usage_key).save()
        CourseAggregatedMetaData(id=course_key, total_assessments=10, total_modules=20).save()
        CourseStructure(course_id=course_key, structure_json='{"test": true}').save()
        CourseOverview.get_from_id(course_key)

    def assert_reference_data_exists(self, course_id):
        """
        Asserts course reference data exists in DB
        """
        self.assertEqual(1, CourseGroupRelationship.objects.filter(course_id=course_id).count())
        self.assertEqual(1, StudentGradebook.objects.filter(course_id=course_id).count())
        self.assertEqual(1, StudentProgress.objects.filter(course_id=course_id).count())
        self.assertEqual(1, CourseModuleCompletion.objects.filter(course_id=course_id).count())
        self.assertEqual(1, CourseEnrollment.objects.filter(course_id=course_id).count())
        self.assertEqual(1, CourseAccessRole.objects.filter(course_id=course_id).count())
        self.assertEqual(1, StudentModule.objects.filter(course_id=course_id).count())
        self.assertEqual(1, CourseAggregatedMetaData.objects.filter(id=course_id).count())
        self.assertEqual(1, CourseOverview.objects.filter(id=course_id).count())
        self.assertEqual(1, CourseStructure.objects.filter(course_id=course_id).count())

        course = modulestore().get_course(course_id)
        self.assertIsNotNone(course)
        self.assertEqual(unicode(course_id), unicode(course.id))

    def assert_reference_data_deleted(self, course_id):
        """
        Asserts course reference data deleted in DB
        """
        self.assertEqual(0, CourseGroupRelationship.objects.filter(course_id=course_id).count())
        self.assertEqual(0, StudentGradebook.objects.filter(course_id=course_id).count())
        self.assertEqual(0, StudentProgress.objects.filter(course_id=course_id).count())
        self.assertEqual(0, CourseModuleCompletion.objects.filter(course_id=course_id).count())
        self.assertEqual(0, CourseEnrollment.objects.filter(course_id=course_id).count())
        self.assertEqual(0, CourseAccessRole.objects.filter(course_id=course_id).count())
        self.assertEqual(0, StudentModule.objects.filter(course_id=course_id).count())
        self.assertEqual(0, CourseAggregatedMetaData.objects.filter(id=course_id).count())
        self.assertEqual(0, CourseOverview.objects.filter(id=course_id).count())
        self.assertEqual(0, CourseStructure.objects.filter(course_id=course_id).count())

        course = modulestore().get_course(course_id)
        self.assertIsNone(course)

    def setup_course_data(self, number_of_courses=1, days_ago=60):
        """
        Creates courses and reference data to test and return list of course ids created
        """
        course_ids = []
        past_datetime = datetime.now(pytz.UTC) + timedelta(days=-days_ago)
        with freeze_time(past_datetime):
            while len(course_ids) < number_of_courses:
                course = BulkCourseDeleteTests.create_course()
                BulkCourseDeleteTests.create_course_reference_data(course.id)
                course_ids.append(course.id)
        return course_ids

    def test_course_bulk_delete(self):
        """
        Test bulk course deletion
        """
        # Set up courses and data to be deleted
        course_ids = self.setup_course_data(number_of_courses=4)

        # assert data exists
        for course_id in course_ids:
            self.assert_reference_data_exists(course_id)

        with mock.patch(self.YESNO_PATCH_LOCATION) as patched_yes_no:
            patched_yes_no.return_value = True
            call_command('bulk_delete_courses_with_reference_data', age=60)

        # assert data deleted
        for course_id in course_ids:
            self.assert_reference_data_deleted(course_id)

    def test_course_bulk_delete_with_no_prompt(self):
        """
        Test bulk course deletion when user opt to type `No` when prompted
        """
        # Set up courses and data to be deleted
        course_ids = self.setup_course_data()

        with mock.patch(self.YESNO_PATCH_LOCATION) as patched_yes_no:
            patched_yes_no.return_value = False
            call_command('bulk_delete_courses_with_reference_data', age=60)

        # assert data still exists
        for course_id in course_ids:
            self.assert_reference_data_exists(course_id)

    def test_course_bulk_delete_without_age(self):
        """
        Test bulk course deletion when age option is not given
        """
        # Set up courses and data to be deleted
        course_ids = self.setup_course_data()

        with self.assertRaises(SystemExit):
            call_command('bulk_delete_courses_with_reference_data')

        # assert data still exists
        for course_id in course_ids:
            self.assert_reference_data_exists(course_id)

    def test_course_bulk_delete_with_non_int_age(self):
        """
        Test bulk course deletion when age option is not an integer
        """
        # Set up courses and data to be deleted
        course_ids = self.setup_course_data()

        with self.assertRaises(ValueError):
            call_command('bulk_delete_courses_with_reference_data', age='junk')

        # assert data still exists
        for course_id in course_ids:
            self.assert_reference_data_exists(course_id)

    def test_course_bulk_delete_with_no_edited_on(self):
        """
        Test bulk course deletion when course has no edited_on attribute
        """
        # Set up courses and data to be deleted
        course_ids = self.setup_course_data(number_of_courses=2, days_ago=90)

        with mock.patch(self.YESNO_PATCH_LOCATION) as patched_yes_no:
            patched_yes_no.return_value = True
            with mock.patch.object(
                CourseDescriptor, 'edited_on', create=True, new_callable=PropertyMock
            ) as mocked_edited_on:
                mocked_edited_on.return_value = None
                call_command('bulk_delete_courses_with_reference_data', age=60)

        # assert data still exists
        for course_id in course_ids:
            self.assert_reference_data_exists(course_id)
