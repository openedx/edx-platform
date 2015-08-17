"""
Tests for the lms_filter_generator
"""
from mock import patch, Mock

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from student.tests.factories import UserFactory
from student.models import CourseEnrollment

from xmodule.partitions.partitions import Group, UserPartition
from openedx.core.djangoapps.course_groups.partition_scheme import CohortPartitionScheme
from openedx.core.djangoapps.user_api.partition_schemes import RandomUserPartitionScheme
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory, config_course_cohorts
from openedx.core.djangoapps.course_groups.cohorts import add_user_to_cohort
from openedx.core.djangoapps.course_groups.views import link_cohort_to_partition_group
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
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

        self.chapter2 = ItemFactory.create(
            parent_location=self.courses[1].location,
            category='chapter',
            display_name="Week 1",
            publish_item=True,
        )

        self.groups = [Group(1, 'Group 1'), Group(2, 'Group 2')]

        self.content_groups = [1, 2]

    def setUp(self):
        super(LmsSearchFilterGeneratorTestCase, self).setUp()
        self.build_courses()
        self.user = UserFactory.create(username="jack", email="jack@fake.edx.org", password='test')

        for course in self.courses:
            CourseEnrollment.enroll(self.user, course.location.course_key)

    def test_course_id_not_provided(self):
        """
        Tests that we get the list of IDs of courses the user is enrolled in when the course ID is null or not provided
        """
        field_dictionary, filter_dictionary, _ = LmsSearchFilterGenerator.generate_field_filters(user=self.user)

        self.assertTrue('start_date' in filter_dictionary)
        self.assertIn(unicode(self.courses[0].id), field_dictionary['course'])
        self.assertIn(unicode(self.courses[1].id), field_dictionary['course'])

    def test_course_id_provided(self):
        """
        Tests that we get the course ID when the course ID is provided
        """
        field_dictionary, filter_dictionary, _ = LmsSearchFilterGenerator.generate_field_filters(
            user=self.user,
            course_id=unicode(self.courses[0].id)
        )

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(unicode(self.courses[0].id), field_dictionary['course'])

    def test_user_not_provided(self):
        """
        Tests that we get empty list of courses in case the user is not provided
        """
        field_dictionary, filter_dictionary, _ = LmsSearchFilterGenerator.generate_field_filters()

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(0, len(field_dictionary['course']))

    def test_excludes_microsite(self):
        """ By default there is the test microsite to exclude """
        _, _, exclude_dictionary = LmsSearchFilterGenerator.generate_field_filters(user=self.user)
        self.assertIn('org', exclude_dictionary)
        exclude_orgs = exclude_dictionary['org']
        self.assertEqual(1, len(exclude_orgs))
        self.assertEqual('TestMicrositeX', exclude_orgs[0])

    @patch('microsite_configuration.microsite.get_all_orgs', Mock(return_value=[]))
    def test_excludes_no_microsite(self):
        """ Test when no microsite is present - nothing to exclude """
        _, _, exclude_dictionary = LmsSearchFilterGenerator.generate_field_filters(user=self.user)
        self.assertNotIn('org', exclude_dictionary)

    @patch('microsite_configuration.microsite.get_value', Mock(return_value='TestMicrositeX'))
    def test_excludes_microsite_within(self):
        field_dictionary, _, exclude_dictionary = LmsSearchFilterGenerator.generate_field_filters(user=self.user)
        self.assertNotIn('org', exclude_dictionary)
        self.assertIn('org', field_dictionary)
        self.assertEqual('TestMicrositeX', field_dictionary['org'])

    @patch(
        'microsite_configuration.microsite.get_all_orgs',
        Mock(return_value=["TestMicrosite1", "TestMicrosite2", "TestMicrosite3", "TestMicrosite4"])
    )
    def test_excludes_multi_microsites(self):
        _, _, exclude_dictionary = LmsSearchFilterGenerator.generate_field_filters(user=self.user)
        self.assertIn('org', exclude_dictionary)
        exclude_orgs = exclude_dictionary['org']
        self.assertEqual(4, len(exclude_orgs))
        self.assertIn('TestMicrosite1', exclude_orgs)
        self.assertIn('TestMicrosite2', exclude_orgs)
        self.assertIn('TestMicrosite3', exclude_orgs)
        self.assertIn('TestMicrosite4', exclude_orgs)

    @patch(
        'microsite_configuration.microsite.get_all_orgs',
        Mock(return_value=["TestMicrosite1", "TestMicrosite2", "TestMicrosite3", "TestMicrosite4"])
    )
    @patch('microsite_configuration.microsite.get_value', Mock(return_value='TestMicrosite3'))
    def test_excludes_multi_microsites_within(self):
        field_dictionary, _, exclude_dictionary = LmsSearchFilterGenerator.generate_field_filters(user=self.user)
        self.assertNotIn('org', exclude_dictionary)
        self.assertIn('org', field_dictionary)
        self.assertEqual('TestMicrosite3', field_dictionary['org'])


class LmsSearchFilterGeneratorGroupsTestCase(LmsSearchFilterGeneratorTestCase):
    """
    Test case class to test search result processor
    with content and user groups present within the course
    """

    def setUp(self):
        super(LmsSearchFilterGeneratorGroupsTestCase, self).setUp()
        self.user_partition = None
        self.split_test_user_partition = None
        self.first_cohort = None
        self.second_cohort = None

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

    def add_split_test(self, groups=None):
        """
        Adds split test and two content groups to second course in courses list.
        """
        if groups is None:
            groups = self.groups

        self.split_test_user_partition = UserPartition(
            id=0,
            name='Partition 2',
            description='This is partition 2',
            groups=groups,
            scheme=RandomUserPartitionScheme
        )

        self.split_test_user_partition.scheme.name = "random"

        sequential = ItemFactory.create(
            parent_location=self.chapter.location,
            category='sequential',
            display_name="Lesson 2",
            publish_item=True,
        )

        vertical = ItemFactory.create(
            parent_location=sequential.location,
            category='vertical',
            display_name='Subsection 3',
            publish_item=True,
        )

        split_test_unit = ItemFactory.create(
            parent_location=vertical.location,
            category='split_test',
            user_partition_id=0,
            display_name="Test Content Experiment 1",
        )

        condition_1_vertical = ItemFactory.create(
            parent_location=split_test_unit.location,
            category="vertical",
            display_name="Group ID 1",
        )

        condition_2_vertical = ItemFactory.create(
            parent_location=split_test_unit.location,
            category="vertical",
            display_name="Group ID 2",
        )

        ItemFactory.create(
            parent_location=condition_1_vertical.location,
            category="html",
            display_name="Group A",
            publish_item=True,
        )

        ItemFactory.create(
            parent_location=condition_2_vertical.location,
            category="html",
            display_name="Group B",
            publish_item=True,
        )

        self.courses[1].user_partitions = [self.split_test_user_partition]
        self.courses[1].save()
        modulestore().update_item(self.courses[1], self.user.id)

    def add_user_to_splittest_group(self):
        """
        adds user to a random split test group
        """
        self.split_test_user_partition.scheme.get_group_for_user(
            CourseKey.from_string(unicode(self.courses[1].id)),
            self.user,
            self.split_test_user_partition,
            assign=True,
        )

        self.courses[1].save()
        modulestore().update_item(self.courses[1], self.user.id)

    def test_content_group_id_provided(self):
        """
        Tests that we get the content group ID when course is assigned to cohort
        which is assigned content group.
        """
        self.add_seq_with_content_groups()
        self.add_user_to_cohort_group()
        field_dictionary, filter_dictionary, _ = LmsSearchFilterGenerator.generate_field_filters(
            user=self.user,
            course_id=unicode(self.courses[0].id)
        )

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(unicode(self.courses[0].id), field_dictionary['course'])
        self.assertEqual([unicode(self.content_groups[0])], filter_dictionary['content_groups'])

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

        field_dictionary, filter_dictionary, _ = LmsSearchFilterGenerator.generate_field_filters(
            user=self.user,
            course_id=unicode(self.courses[0].id)
        )

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(unicode(self.courses[0].id), field_dictionary['course'])
        # returns only first group, relevant to current user
        self.assertEqual([unicode(self.content_groups[0])], filter_dictionary['content_groups'])

    def test_content_group_id_not_provided(self):
        """
        Tests that we don't get content group ID when course is assigned a cohort
        but cohort is not assigned to content group.
        """
        self.add_seq_with_content_groups(groups=[])

        field_dictionary, filter_dictionary, _ = LmsSearchFilterGenerator.generate_field_filters(
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

        field_dictionary, filter_dictionary, _ = LmsSearchFilterGenerator.generate_field_filters(
            user=self.user,
            course_id=unicode(self.courses[0].id)
        )

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(unicode(self.courses[0].id), field_dictionary['course'])
        self.assertEqual(None, filter_dictionary['content_groups'])

    def test_split_test_with_user_groups_user_not_assigned(self):
        """
        Tests that we don't get user group ID when user is not assigned to a split test group
        """
        self.add_split_test()

        field_dictionary, filter_dictionary, _ = LmsSearchFilterGenerator.generate_field_filters(
            user=self.user,
            course_id=unicode(self.courses[1].id)
        )

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(unicode(self.courses[1].id), field_dictionary['course'])
        self.assertEqual(None, filter_dictionary['content_groups'])

    def test_split_test_with_user_groups_user_assigned(self):
        """
        Tests that we get user group ID when user is assigned to a split test group
        """
        self.add_split_test()
        self.add_user_to_splittest_group()

        field_dictionary, filter_dictionary, _ = LmsSearchFilterGenerator.generate_field_filters(
            user=self.user,
            course_id=unicode(self.courses[1].id)
        )

        partition_group = self.split_test_user_partition.scheme.get_group_for_user(
            CourseKey.from_string(unicode(self.courses[1].id)),
            self.user,
            self.split_test_user_partition,
            assign=False,
        )

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(unicode(self.courses[1].id), field_dictionary['course'])
        self.assertEqual([unicode(partition_group.id)], filter_dictionary['content_groups'])

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
