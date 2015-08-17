"""
Test for split test XModule
"""
from django.core.urlresolvers import reverse
from mock import MagicMock
from nose.plugins.attrib import attr

from courseware.module_render import get_module_for_descriptor
from courseware.model_data import FieldDataCache
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.factories import ItemFactory, CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.partitions.partitions import Group, UserPartition
from openedx.core.djangoapps.user_api.tests.factories import UserCourseTagFactory


@attr('shard_1')
class SplitTestBase(ModuleStoreTestCase):
    """
    Sets up a basic course and user for split test testing.
    Also provides tests of rendered HTML for two user_tag conditions, 0 and 1.
    """
    __test__ = False
    COURSE_NUMBER = 'split-test-base'
    ICON_CLASSES = None
    TOOLTIPS = None
    HIDDEN_CONTENT = None
    VISIBLE_CONTENT = None

    def setUp(self):
        super(SplitTestBase, self).setUp()
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
        """
        Returns a video component with parent ``parent``
        that is intended to be displayed to group ``group``.
        """
        return ItemFactory.create(
            parent_location=parent.location,
            category="video",
            display_name="Group {} Sees This Video".format(group),
        )

    def _problem(self, parent, group):
        """
        Returns a problem component with parent ``parent``
        that is intended to be displayed to group ``group``.
        """
        return ItemFactory.create(
            parent_location=parent.location,
            category="problem",
            display_name="Group {} Sees This Problem".format(group),
            data="<h1>No Problem Defined Yet!</h1>",
        )

    def _html(self, parent, group):
        """
        Returns an html component with parent ``parent``
        that is intended to be displayed to group ``group``.
        """
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
        """Checks that the right compentents are rendered for user with ``user_tag``"""
        # This explicitly sets the user_tag for self.student to ``user_tag``
        UserCourseTagFactory(
            user=self.student,
            course_id=self.course.id,
            key='xblock.partition_service.partition_{0}'.format(self.partition.id),
            value=str(user_tag)
        )

        resp = self.client.get(reverse(
            'courseware_section',
            kwargs={'course_id': self.course.id.to_deprecated_string(),
                    'chapter': self.chapter.url_name,
                    'section': self.sequential.url_name}
        ))
        content = resp.content

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

    COURSE_NUMBER = 'vert-split-vert'

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
        # We define problem compenents that we need but don't explicitly call elsewhere.
        # pylint: disable=unused-variable
        super(TestVertSplitTestVert, self).setUp()

        # vert <- split_test
        # split_test cond 0 = vert <- {video, problem}
        # split_test cond 1 = vert <- {video, html}
        vert1 = ItemFactory.create(
            parent_location=self.sequential.location,
            category="vertical",
            display_name="Split test vertical",
        )
        # pylint: disable=protected-access
        c0_url = self.course.id.make_usage_key("vertical", "split_test_cond0")
        c1_url = self.course.id.make_usage_key("vertical", "split_test_cond1")

        split_test = ItemFactory.create(
            parent_location=vert1.location,
            category="split_test",
            display_name="Split test",
            user_partition_id='0',
            group_id_to_child={"0": c0_url, "1": c1_url},
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
        # We define problem compenents that we need but don't explicitly call elsewhere.
        # pylint: disable=unused-variable
        super(TestSplitTestVert, self).setUp()

        # split_test cond 0 = vert <- {video, problem}
        # split_test cond 1 = vert <- {video, html}
        # pylint: disable=protected-access
        c0_url = self.course.id.make_usage_key("vertical", "split_test_cond0")
        c1_url = self.course.id.make_usage_key("vertical", "split_test_cond1")

        split_test = ItemFactory.create(
            parent_location=self.sequential.location,
            category="split_test",
            display_name="Split test",
            user_partition_id='0',
            group_id_to_child={"0": c0_url, "1": c1_url},
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


@attr('shard_1')
class SplitTestPosition(ModuleStoreTestCase):
    """
    Check that we can change positions in a course with partitions defined
    """
    def setUp(self):
        super(SplitTestPosition, self).setUp()

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
            user_partitions=[self.partition]
        )

        self.chapter = ItemFactory.create(
            parent_location=self.course.location,
            category="chapter",
            display_name="test chapter",
        )

        self.student = UserFactory.create()
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)
        self.client.login(username=self.student.username, password='test')

    def test_changing_position_works(self):
        # Make a mock FieldDataCache for this course, so we can get the course module
        mock_field_data_cache = FieldDataCache([self.course], self.course.id, self.student)
        course = get_module_for_descriptor(
            self.student,
            MagicMock(name='request'),
            self.course,
            mock_field_data_cache,
            self.course.id,
            course=self.course
        )

        # Now that we have the course, change the position and save, nothing should explode!
        course.position = 2
        course.save()
