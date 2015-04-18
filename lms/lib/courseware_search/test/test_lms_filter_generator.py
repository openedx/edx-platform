"""
Tests for the lms_filter_generator
"""
from mock import patch
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from student.tests.factories import UserFactory
from student.models import CourseEnrollment

from lms.lib.courseware_search.lms_filter_generator import LmsSearchFilterGenerator
from xmodule.partitions.partitions import Group, UserPartition
from xmodule.partitions.tests.test_partitions import MockUserPartitionScheme
from openedx.core.djangoapps.course_groups.models import CourseCohort
from opaque_keys import InvalidKeyError


class LmsSearchFilterGeneratorTestCase(ModuleStoreTestCase):
    """ Test case class to test search result processor """

    def build_courses(self):
        """
        Build up a course tree with multiple test courses
        """

        self.courses = [
            CourseFactory.create(
                org='ElasticsearchFiltering',
                course='ES101F',
                run='test_run',
                display_name='Elasticsearch Filtering test course',
            ),

            CourseFactory.create(
                org='FilterTest',
                course='FT101',
                run='test_run',
                display_name='FilterTest test course',
            )
        ]

        self.chapter = ItemFactory.create(
            parent_location=self.courses[0].location,
            category='chapter',
            display_name="Week 1",
            publish_item=True,
        )

        self.content_groups = [1, 2]

    def setUp(self):
        super(LmsSearchFilterGeneratorTestCase, self).setUp()
        self.build_courses()
        self.user = UserFactory.create(username="jack", email="jack@fake.edx.org", password='test')
        for course in self.courses:
            CourseEnrollment.enroll(self.user, course.location.course_key)

    def add_seq_with_content_groups(self):
        """
        Adds sequential and two content groups to first course in courses list.
        """
        user_partitions_json = UserPartition(
            0,
            'Partition 1',
            'This is partition 1',
            [Group("2", 'Group 2'), Group("1", 'Group 1')],
            MockUserPartitionScheme("cohort")
        ).to_json()

        ItemFactory.create(
            parent_location=self.chapter.location,
            category='sequential',
            display_name="Lesson 1",
            publish_item=True,
            metadata={u"user_partitions": [user_partitions_json]}
        )

    def test_course_id_not_provided(self):
        """
        Tests that we get the list of IDs of courses the user is enrolled in when the course ID is null or not provided
        """
        field_dictionary, filter_dictionary = LmsSearchFilterGenerator.generate_field_filters(user=self.user)

        self.assertTrue('start_date' in filter_dictionary)
        self.assertIn(unicode(self.courses[0].id), field_dictionary['course'])
        self.assertIn(unicode(self.courses[1].id), field_dictionary['course'])

    def test_course_id_provided(self):
        """
        Tests that we get the course ID when the course ID is provided
        """
        field_dictionary, filter_dictionary = LmsSearchFilterGenerator.generate_field_filters(
            user=self.user,
            course_id=unicode(self.courses[0].id)
        )

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(unicode(self.courses[0].id), field_dictionary['course'])

    def test_user_not_provided(self):
        """
        Tests that we get empty list of courses in case the user is not provided
        """
        field_dictionary, filter_dictionary = LmsSearchFilterGenerator.generate_field_filters()

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(0, len(field_dictionary['course']))

    @patch('openedx.core.djangoapps.course_groups.cohorts.get_cohort')
    @patch('openedx.core.djangoapps.course_groups.models.CourseUserGroupPartitionGroup.objects.get')
    def test_content_group_id_provided(self, mock_get, mock_get_cohort):
        """
        Tests that we get the content group ID when course is assigned to cohort
        which is assigned content group.
        """
        mock_get_cohort.return_value = CourseCohort.create(
            cohort_name='Cohort 1',
            course_id=self.courses[0].id,
            assignment_type=CourseCohort.RANDOM
        )

        returned_groups = type("CourseGroups", (object, ), dict(group_id=1))
        mock_get.return_value = returned_groups

        self.add_seq_with_content_groups()

        field_dictionary, filter_dictionary = LmsSearchFilterGenerator.generate_field_filters(
            user=self.user,
            course_id=unicode(self.courses[0].id)
        )

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(unicode(self.courses[0].id), field_dictionary['course'])
        self.assertEqual(unicode(self.content_groups[0]), filter_dictionary['content_groups'])

    @patch('openedx.core.djangoapps.course_groups.cohorts.get_cohort')
    @patch('openedx.core.djangoapps.course_groups.models.CourseUserGroupPartitionGroup.objects.get')
    def test_content_multiple_groups_id_provided(self, mock_get, mock_get_cohort):
        """
        Tests that we get content groups IDs when course is assigned to cohort
        which is assigned to multiple content groups.
        """
        mock_get_cohort.return_value = CourseCohort.create(
            cohort_name='Cohort 1',
            course_id=self.courses[0].id,
            assignment_type=CourseCohort.RANDOM
        )

        returned_groups = type("CourseGroups", (object, ), dict(group_id=[1, 2]))
        mock_get.return_value = returned_groups

        self.add_seq_with_content_groups()

        field_dictionary, filter_dictionary = LmsSearchFilterGenerator.generate_field_filters(
            user=self.user,
            course_id=unicode(self.courses[0].id)
        )

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(unicode(self.courses[0].id), field_dictionary['course'])
        self.assertEqual(unicode(self.content_groups), filter_dictionary['content_groups'])

    @patch('openedx.core.djangoapps.course_groups.cohorts.get_cohort')
    def test_content_group_id_not_provided(self, mock_get_cohort):
        """
        Tests that we don't get content group ID when course is assigned a cohort
        but cohort is not assigned to content group.
        """
        mock_get_cohort.return_value = CourseCohort.create(
            cohort_name='Cohort 1',
            course_id=self.courses[0].id,
            assignment_type=CourseCohort.RANDOM
        )

        self.add_seq_with_content_groups()

        field_dictionary, filter_dictionary = LmsSearchFilterGenerator.generate_field_filters(
            user=self.user,
            course_id=unicode(self.courses[0].id)
        )

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(unicode(self.courses[0].id), field_dictionary['course'])
        self.assertEqual(unicode(None), filter_dictionary['content_groups'])

    def test_content_group_with_cohort_not_provided(self):
        """
        Tests that we don't get content group ID when course has no cohorts
        """
        self.add_seq_with_content_groups()

        field_dictionary, filter_dictionary = LmsSearchFilterGenerator.generate_field_filters(
            user=self.user,
            course_id=unicode(self.courses[0].id)
        )

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(unicode(self.courses[0].id), field_dictionary['course'])
        self.assertEqual(unicode(None), filter_dictionary['content_groups'])

    @patch('opaque_keys.edx.keys.CourseKey.from_string')
    @patch('opaque_keys.edx.locations.SlashSeparatedCourseKey.from_deprecated_string')
    def test_type_error_course_key(self, mock_from_deprecated_string, mock_from_string):
        """
        Test system raises an error if no cohort found.
        """
        # set mocked exception response
        err = InvalidKeyError
        mock_from_string.return_value = err
        mock_from_deprecated_string.return_value = err

        self.add_seq_with_content_groups()
        with self.assertRaises(TypeError):
            LmsSearchFilterGenerator.generate_field_filters(
                user=self.user,
                course_id=unicode(self.courses[0].id)
            )

    def test_invalid_course_key(self):
        """
        Test system raises an error if no course found.
        """

        self.add_seq_with_content_groups()
        with self.assertRaises(InvalidKeyError):
            LmsSearchFilterGenerator.generate_field_filters(
                user=self.user,
                course_id='this_is_false_course_id'
            )
