"""
Test for split test XModule
"""
import ddt
from mock import MagicMock, patch, Mock
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from student.tests.factories import UserFactory, CourseEnrollmentFactory, AdminFactory
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from xmodule.modulestore.tests.factories import ItemFactory, CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.partitions.partitions import Group, UserPartition
from xmodule.partitions.test_partitions import StaticPartitionService
from user_api.tests.factories import UserCourseTagFactory
from xmodule.partitions.partitions import Group, UserPartition


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
@ddt.ddt
class TestVertSplitTestVert(ModuleStoreTestCase):
    """
    Tests related to xmodule/split_test_module
    """

    def setUp(self):

        self.partition = UserPartition(0, 'first_partition', 'First Partition', [Group("0", 'alpha'), Group("1", 'beta')])

        self.course = CourseFactory.create(
            user_partitions=[self.partition]
        )

        self.chapter = ItemFactory.create(
            parent_location=self.course.location,
            category="chapter",
            display_name="test chapter",
        )
        self.sequential = ItemFactory.create(
            parent_location=self.chapter.location,
            category="sequential",
            display_name="Split Test Tests",
        )

        # vert <- split_test
        # split_test cond 0 = vert <- {video, problem}
        # split_test cond 1 = vert <- {video, html}
        vert1 = ItemFactory.create(
            parent_location=self.sequential.location,
            category="vertical",
            display_name="Split test vertical",
        )
        c0_url = self.course.location._replace(category="vertical", name="split_test_cond0")
        c1_url = self.course.location._replace(category="vertical", name="split_test_cond1")

        split_test = ItemFactory.create(
            parent_location=vert1.location,
            category="split_test",
            display_name="Split test",
            user_partition_id='0',
            group_id_to_child={"0": c0_url.url(), "1": c1_url.url()},
        )

        cond0vert = ItemFactory.create(
            parent_location=split_test.location,
            category="vertical",
            display_name="Condition 0 vertical",
            location=c0_url,
        )
        video0 = ItemFactory.create(
            parent_location=cond0vert.location,
            category="video",
            display_name="Group 0 Sees This Video",
        )
        problem0 = ItemFactory.create(
            parent_location=cond0vert.location,
            category="problem",
            display_name="Group 0 Sees This Problem",
            data="<h1>No Problem Defined Yet!</h1>",
        )
        self.cond0data = {
            'button_class': '<a class="seq_problem inactive progress-0"',
            'tooltips': ['Group 0 Sees This Video', "Group 0 Sees This Problem"],
            'vertical_name': 'Condition 0 vertical',
            'data': "",  # problems are json loaded so we won't see content
        }

        cond1vert = ItemFactory.create(
            parent_location=split_test.location,
            category="vertical",
            display_name="Condition 1 vertical",
            location=c1_url,
        )
        video1 = ItemFactory.create(
            parent_location=cond1vert.location,
            category="video",
            display_name="Group 1 Sees This Video",
        )
        html1 = ItemFactory.create(
            parent_location=cond1vert.location,
            category="html",
            display_name="Group 1 Sees This HTML",
            data="Some HTML",
        )
        self.cond1data = {
            'button_class': '<a class="seq_video inactive progress-0"',
            'tooltips': ['Group 1 Sees This Video', 'Group 1 Sees This HTML'],
            'vertical_name': 'Condition 1 vertical',
            'data': 'Some HTML',
        }

        self.student = UserFactory.create()
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)
        self.client.login(username=self.student.username, password='test')

    @ddt.data(('0',), ('1',))
    @ddt.unpack
    def test_split_nested_verticals(self, user_tag):
        tag_factory = UserCourseTagFactory(
            user=self.student,
            course_id=self.course.id,
            key='xblock.partition_service.partition_{0}'.format(self.partition.id),
            value=user_tag
        )
        data = self.cond0data
        if user_tag == '1':
            data = self.cond1data

        resp = self.client.get(reverse('courseware_section',
                                       kwargs={'course_id': self.course.id,
                                               'chapter': self.chapter.url_name,
                                               'section': self.sequential.url_name}
        ))

        content = resp.content

        # Assert we see the proper icon in the top display
        self.assertIn(data['button_class'], content)
        # And proper tooltips
        for tooltip in data['tooltips']:
            self.assertIn(tooltip, content)
        self.assertNotIn(data['vertical_name'], content)
        # Assert that we can see the data from the appropriate test condition
        self.assertIn(data['data'], content)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
@ddt.ddt
class TestSplitTestVert(ModuleStoreTestCase):
    """
    Tests related to xmodule/split_test_module
    """

    def setUp(self):

        self.partition = UserPartition(0, 'first_partition', 'First Partition', [Group("0", 'alpha'), Group("1", 'beta')])

        self.course = CourseFactory.create(
            user_partitions=[self.partition]
        )

        self.chapter = ItemFactory.create(
            parent_location=self.course.location,
            category="chapter",
            display_name="test chapter",
        )
        self.sequential = ItemFactory.create(
            parent_location=self.chapter.location,
            category="sequential",
            display_name="Split Test Tests",
        )

        # split_test cond 0 = vert <- {video, problem}
        # split_test cond 1 = vert <- {video, html}
        c0_url = self.course.location._replace(category="split_test", name="split_test_cond0")
        c1_url = self.course.location._replace(category="split_test", name="split_test_cond1")

        split_test = ItemFactory.create(
            parent_location=vert1.location,
            category="split_test",
            display_name="Split test",
            user_partition_id='0',
            group_id_to_child={"0": c0_url.url(), "1": c1_url.url()},
        )

        cond0vert = ItemFactory.create(
            parent_location=split_test.location,
            category="vertical",
            display_name="Condition 0 vertical",
            location=c0_url,
        )
        video0 = ItemFactory.create(
            parent_location=cond0vert.location,
            category="video",
            display_name="Group 0 Sees This Video",
        )
        problem0 = ItemFactory.create(
            parent_location=cond0vert.location,
            category="problem",
            display_name="Group 0 Sees This Problem",
            data="<h1>No Problem Defined Yet!</h1>",
        )
        self.cond0data = {
            'button_class': '<a class="seq_problem inactive progress-0"',
            'tooltips': ['Group 0 Sees This Video', "Group 0 Sees This Problem"],
            'vertical_name': 'Condition 0 vertical',
            'data': "",  # problems are json loaded so we won't see content
        }

        cond1vert = ItemFactory.create(
            parent_location=split_test.location,
            category="vertical",
            display_name="Condition 1 vertical",
            location=c1_url,
        )
        video1 = ItemFactory.create(
            parent_location=cond1vert.location,
            category="video",
            display_name="Group 1 Sees This Video",
        )
        html1 = ItemFactory.create(
            parent_location=cond1vert.location,
            category="html",
            display_name="Group 1 Sees This HTML",
            data="Some HTML",
        )
        self.cond1data = {
            'button_class': '<a class="seq_video inactive progress-0"',
            'tooltips': ['Group 1 Sees This Video', 'Group 1 Sees This HTML'],
            'vertical_name': 'Condition 1 vertical',
            'data': 'Some HTML',
        }

        self.student = UserFactory.create()
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)
        self.client.login(username=self.student.username, password='test')

    @ddt.data(('0',), ('1',))
    @ddt.unpack
    def test_split_nested_verticals(self, user_tag):
        tag_factory = UserCourseTagFactory(
            user=self.student,
            course_id=self.course.id,
            key='xblock.partition_service.partition_{0}'.format(self.partition.id),
            value=user_tag
        )
        data = self.cond0data
        if user_tag == '1':
            data = self.cond1data

        resp = self.client.get(reverse('courseware_section',
                                       kwargs={'course_id': self.course.id,
                                               'chapter': self.chapter.url_name,
                                               'section': self.sequential.url_name}
        ))

        content = resp.content

        # Assert we see the proper icon in the top display
        self.assertIn(data['button_class'], content)
        # And proper tooltips
        for tooltip in data['tooltips']:
            self.assertIn(tooltip, content)
        self.assertNotIn(data['vertical_name'], content)
        # Assert that we can see the data from the appropriate test condition
        self.assertIn(data['data'], content)
