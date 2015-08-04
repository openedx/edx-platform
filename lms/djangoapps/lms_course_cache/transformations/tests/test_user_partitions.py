"""
Tests for UserPartitionTransformation.
"""
from unittest import TestCase
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

from lms_course_cache.transformations.user_partitions import UserPartitionTransformation
from lms_course_cache.api import get_course_blocks, clear_course_from_cache


class UserPartitionTransformationTestCase(ModuleStoreTestCase):
    """ Test case class to test search result processor """

    def build_course(self):
        """
        Build up a course tree with multiple test courses
        """

        self.course = CourseFactory.create(
            org='UserPartitionTransformation',
            course='UP101F',
            run='test_run',
            display_name='User Partition Transformation test course',
        )
        self.course.save()
        self.chapter = ItemFactory.create(
            parent=self.course,
            category='chapter',
            display_name="Week 1",
            publish_item=True,
        )
        self.chapter.save()
        self.sequential = ItemFactory.create(
            parent=self.chapter,
            category='sequential',
            display_name="Lesson 1",
            publish_item=True,
        )
        self.sequential.save()
        self.vertical = ItemFactory.create(
            parent=self.sequential,
            category='vertical',
            display_name='Subsection 1',
            publish_item=True,
        )
        self.vertical.save()
        self.html = ItemFactory.create(
            parent=self.vertical,
            category='html',
            display_name='Html Test 1',
            publish_item=True,          
        )

        self.groups = [Group(1, 'Group 1'), Group(2, 'Group 2')]

        self.content_groups = [1, 2]

    def setUp(self):
        super(UserPartitionTransformationTestCase, self).setUp()
        self.build_course()
        self.user = UserFactory.create(username="jack", email="jack@fake.edx.org", password='test')
        self.user_partition = None
        self.first_cohort = None
        self.second_cohort = None

        CourseEnrollment.enroll(self.user, self.course.location.course_key)
        self.course.save()
        modulestore().update_item(self.course, self.user.id)

    def add_seq_with_content_groups(self, groups=None):
        """
        Adds sequential and two content groups to first course in courses list.
        """
        config_course_cohorts(self.course, is_cohorted=True)

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

        self.html2 = ItemFactory.create(
            parent=self.vertical,
            category='html',
            display_name="Html Test 2",
            publish_item=True,
            metadata={'group_access': {0: [1]}},
        )
        self.html2.save()
        self.first_cohort, self.second_cohort = [
            CohortFactory(course_id=self.course.id) for _ in range(2)
        ]

        self.course.user_partitions = [self.user_partition]
        self.course.save()
        modulestore().update_item(self.course, self.user.id)

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
        self.course.save()
        self.chapter.save()
        self.sequential.save()
        self.vertical.save()
        self.html.save()
        self.html2.save()
        modulestore().update_item(self.course, self.user.id)
        modulestore().update_item(self.chapter, self.user.id)
        modulestore().update_item(self.sequential, self.user.id)
        modulestore().update_item(self.vertical, self.user.id)
        modulestore().update_item(self.html, self.user.id)
        modulestore().update_item(self.html2, self.user.id)

    # def test_course_structure_without_user_partition(self):
    #     clear_course_from_cache(self.course.id)
    #     self.transformation = UserPartitionTransformation()
    #     course_blocks = get_course_blocks(self.user, self.course.id, transformations={self.transformation})
    #     self.assertEquals(1, course_blocks)

    # def test_course_structure_with_user_partition_not_enrolled(self):
    #     clear_course_from_cache(self.course.id)
    #     self.transformation = UserPartitionTransformation()
    #     self.add_seq_with_content_groups()
    #     course_blocks = get_course_blocks(self.user, self.course.id, transformations={self.transformation})
    #     self.assertEquals(1, course_blocks)

    def test_course_structure_with_user_partition_enrolled(self):
        clear_course_from_cache(self.course.id)
        self.transformation = UserPartitionTransformation()
        self.add_seq_with_content_groups()
        self.add_user_to_cohort_group()

        __, raw_data_blocks = get_course_blocks(
            self.user,
            self.course.id,
            transformations={}
        )
        self.assertEquals(len(raw_data_blocks), 6)

        clear_course_from_cache(self.course.id)
        __, trans_data_blocks = get_course_blocks(
            self.user,
            self.course.id,
            transformations={self.transformation}
        )
        self.assertEquals(len(trans_data_blocks), 5)
