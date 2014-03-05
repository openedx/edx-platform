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
class SplitTestBase(ModuleStoreTestCase):
    __test__ = False

    def setUp(self):
        self.partition = UserPartition(
            0,
            'first_partition',
            'First Partition',
            [
                Group(0, 'alpha'),
                Group(1, 'beta')
            ]
        )

        self.course = CourseFactory.create(
            number=self.COURSE_NUMBER,
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

        self.student = UserFactory.create()
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)
        self.client.login(username=self.student.username, password='test')

    def _video(self, parent, group):
        return ItemFactory.create(
            parent_location=parent.location,
            category="video",
            display_name="Group {} Sees This Video".format(group),
        )

    def _problem(self, parent, group):
        return ItemFactory.create(
            parent_location=parent.location,
            category="problem",
            display_name="Group {} Sees This Problem".format(group),
            data="<h1>No Problem Defined Yet!</h1>",
        )

    def _html(self, parent, group):
        return ItemFactory.create(
            parent_location=parent.location,
            category="html",
            display_name="Group {} Sees This HTML".format(group),
            data="Some HTML for group {}".format(group),
        )

    def test_split_test_0(self):
        self._check_split_test(0)

    def test_split_test_1(self):
        self._check_split_test(1)

    def _check_split_test(self, user_tag):
        tag_factory = UserCourseTagFactory(
            user=self.student,
            course_id=self.course.id,
            key='xblock.partition_service.partition_{0}'.format(self.partition.id),
            value=str(user_tag)
        )

        resp = self.client.get(reverse('courseware_section',
                                       kwargs={'course_id': self.course.id,
                                               'chapter': self.chapter.url_name,
                                               'section': self.sequential.url_name}
        ))

        content = resp.content
        print content

        # Assert we see the proper icon in the top display
        self.assertIn('<a class="{} inactive progress-0"'.format(self.ICON_CLASSES[user_tag]), content)
        # And proper tooltips
        for tooltip in self.TOOLTIPS[user_tag]:
            self.assertIn(tooltip, content)

        for hidden in self.HIDDEN_CONTENT[user_tag]:
            self.assertNotIn(hidden, content)

        # Assert that we can see the data from the appropriate test condition
        for visible in self.VISIBLE_CONTENT[user_tag]:
            self.assertIn(visible, content)


class TestVertSplitTestVert(SplitTestBase):
    """
    Tests related to xmodule/split_test_module
    """
    __test__ = True

    COURSE_NUMBER='vert-split-vert'

    ICON_CLASSES = [
        'seq_problem',
        'seq_video',
    ]
    TOOLTIPS = [
        ['Group 0 Sees This Video', "Group 0 Sees This Problem"],
        ['Group 1 Sees This Video', 'Group 1 Sees This HTML'],
    ]
    HIDDEN_CONTENT = [
        ['Condition 0 vertical'],
        ['Condition 1 vertical'],
    ]

    # Data is html encoded, because it's inactive inside the
    # sequence until javascript is executed
    VISIBLE_CONTENT = [
        ['class=&#34;problems-wrapper'],
        ['Some HTML for group 1']
    ]

    def setUp(self):
        super(TestVertSplitTestVert, self).setUp()

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
        video0 = self._video(cond0vert, 0)
        problem0 = self._problem(cond0vert, 0)

        cond1vert = ItemFactory.create(
            parent_location=split_test.location,
            category="vertical",
            display_name="Condition 1 vertical",
            location=c1_url,
        )
        video1 = self._video(cond1vert, 1)
        html1 = self._html(cond1vert, 1)


class TestSplitTestVert(SplitTestBase):
    """
    Tests related to xmodule/split_test_module
    """
    __test__ = True

    COURSE_NUMBER = 'split-vert'

    ICON_CLASSES = [
        'seq_problem',
        'seq_video',
    ]
    TOOLTIPS = [
        ['Group 0 Sees This Video', "Group 0 Sees This Problem"],
        ['Group 1 Sees This Video', 'Group 1 Sees This HTML'],
    ]
    HIDDEN_CONTENT = [
        ['Condition 0 vertical'],
        ['Condition 1 vertical'],
    ]

    # Data is html encoded, because it's inactive inside the
    # sequence until javascript is executed
    VISIBLE_CONTENT = [
        ['class=&#34;problems-wrapper'],
        ['Some HTML for group 1']
    ]

    def setUp(self):
        super(TestSplitTestVert, self).setUp()

        # split_test cond 0 = vert <- {video, problem}
        # split_test cond 1 = vert <- {video, html}
        c0_url = self.course.location._replace(category="vertical", name="split_test_cond0")
        c1_url = self.course.location._replace(category="vertical", name="split_test_cond1")

        split_test = ItemFactory.create(
            parent_location=self.sequential.location,
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
        video0 = self._video(cond0vert, 0)
        problem0 = self._problem(cond0vert, 0)

        cond1vert = ItemFactory.create(
            parent_location=split_test.location,
            category="vertical",
            display_name="Condition 1 vertical",
            location=c1_url,
        )
        video1 = self._video(cond1vert, 1)
        html1 = self._html(cond1vert, 1)
