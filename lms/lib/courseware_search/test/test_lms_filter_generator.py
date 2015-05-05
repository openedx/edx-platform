"""
Tests for the lms_filter_generator
"""
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from student.tests.factories import UserFactory
from student.models import CourseEnrollment

from xmodule.partitions.partitions import Group, UserPartition
from openedx.core.djangoapps.course_groups.partition_scheme import CohortPartitionScheme
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory, config_course_cohorts
from openedx.core.djangoapps.course_groups.cohorts import add_user_to_cohort
from openedx.core.djangoapps.course_groups.views import link_cohort_to_partition_group
from opaque_keys import InvalidKeyError
from lms.lib.courseware_search.lms_filter_generator import LmsSearchFilterGenerator


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

        self.groups = [Group(1, 'Group 1'), Group(2, 'Group 2')]

        self.content_groups = [1, 2]

    def setUp(self):
        super(LmsSearchFilterGeneratorTestCase, self).setUp()
        self.build_courses()
        self.user_partition = None
        self.first_cohort = None
        self.second_cohort = None
        self.user = UserFactory.create(username="jack", email="jack@fake.edx.org", password='test')

        for course in self.courses:
            CourseEnrollment.enroll(self.user, course.location.course_key)

    def add_seq_with_content_groups(self, groups=None):
        """
        Adds sequential and two content groups to first course in courses list.
        """
        config_course_cohorts(self.courses[0], is_cohorted=True)

        if groups is None:
            groups = self.groups

        self.user_partition = UserPartition(
            id=0,
            name='Partition 1',
            description='This is partition 1',
            groups=groups,
            scheme=CohortPartitionScheme
        )

        self.user_partition.scheme.name = "cohort"

        ItemFactory.create(
            parent_location=self.chapter.location,
            category='sequential',
            display_name="Lesson 1",
            publish_item=True,
            metadata={u"user_partitions": [self.user_partition.to_json()]}
        )

        self.first_cohort, self.second_cohort = [
            CohortFactory(course_id=self.courses[0].id) for _ in range(2)
        ]

        self.courses[0].user_partitions = [self.user_partition]
        self.courses[0].save()
        modulestore().update_item(self.courses[0], self.user.id)

    def add_user_to_cohort_group(self):
        """
        adds user to cohort and links cohort to content group
        """
        add_user_to_cohort(self.first_cohort, self.user.username)

        link_cohort_to_partition_group(
            self.first_cohort,
            self.user_partition.id,
            self.groups[0].id,
        )

        self.courses[0].save()
        modulestore().update_item(self.courses[0], self.user.id)

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

    def test_content_group_id_provided(self):
        """
        Tests that we get the content group ID when course is assigned to cohort
        which is assigned content group.
        """
        self.add_seq_with_content_groups()
        self.add_user_to_cohort_group()
        field_dictionary, filter_dictionary = LmsSearchFilterGenerator.generate_field_filters(
            user=self.user,
            course_id=unicode(self.courses[0].id)
        )

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(unicode(self.courses[0].id), field_dictionary['course'])
        self.assertEqual(unicode(self.content_groups[0]), filter_dictionary['content_groups'])

    def test_content_multiple_groups_id_provided(self):
        """
        Tests that we get content groups IDs when course is assigned to cohort
        which is assigned to multiple content groups.
        """
        self.add_seq_with_content_groups()
        self.add_user_to_cohort_group()

        # Second cohort link
        link_cohort_to_partition_group(
            self.second_cohort,
            self.user_partition.id,
            self.groups[0].id,
        )

        self.courses[0].save()
        modulestore().update_item(self.courses[0], self.user.id)

        field_dictionary, filter_dictionary = LmsSearchFilterGenerator.generate_field_filters(
            user=self.user,
            course_id=unicode(self.courses[0].id)
        )

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(unicode(self.courses[0].id), field_dictionary['course'])
        # returns only first group, relevant to current user
        self.assertEqual(unicode(self.content_groups[0]), filter_dictionary['content_groups'])

    def test_content_group_id_not_provided(self):
        """
        Tests that we don't get content group ID when course is assigned a cohort
        but cohort is not assigned to content group.
        """
        self.add_seq_with_content_groups(groups=[])

        field_dictionary, filter_dictionary = LmsSearchFilterGenerator.generate_field_filters(
            user=self.user,
            course_id=unicode(self.courses[0].id)
        )

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(unicode(self.courses[0].id), field_dictionary['course'])
        self.assertEqual(None, filter_dictionary['content_groups'])

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
        self.assertEqual(None, filter_dictionary['content_groups'])

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
