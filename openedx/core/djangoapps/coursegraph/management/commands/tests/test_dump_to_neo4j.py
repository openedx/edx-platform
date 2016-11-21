# coding=utf-8
"""
Tests for the dump_to_neo4j management command.
"""
from __future__ import unicode_literals

from datetime import datetime

import ddt
import mock
from django.core.management import call_command
from django.utils import six
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j import (
    ModuleStoreSerializer,
)
from openedx.core.djangoapps.coursegraph.management.commands.tests.utils import (
    MockGraph,
    MockNodeSelector,
)
from openedx.core.djangoapps.content.course_structures.signals import (
    listen_for_course_publish
)


class TestDumpToNeo4jCommandBase(SharedModuleStoreTestCase):
    """
    Base class for the test suites in this file. Sets up a couple courses.
    """
    @classmethod
    def setUpClass(cls):
        super(TestDumpToNeo4jCommandBase, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.chapter = ItemFactory.create(parent=cls.course, category='chapter')
        cls.sequential = ItemFactory.create(parent=cls.chapter, category='sequential')
        cls.vertical = ItemFactory.create(parent=cls.sequential, category='vertical')
        cls.html = ItemFactory.create(parent=cls.vertical, category='html')
        cls.problem = ItemFactory.create(parent=cls.vertical, category='problem')
        cls.video = ItemFactory.create(parent=cls.vertical, category='video')
        cls.video2 = ItemFactory.create(parent=cls.vertical, category='video')

        cls.course2 = CourseFactory.create()

        cls.course_strings = [six.text_type(cls.course.id), six.text_type(cls.course2.id)]

    @staticmethod
    def setup_mock_graph(mock_selector_class, mock_graph_class, transaction_errors=False):
        """
        Replaces the py2neo Graph object with a MockGraph; similarly replaces
        NodeSelector with MockNodeSelector.

        Args:
            mock_selector_class: a mocked NodeSelector class
            mock_graph_class: a mocked Graph class
            transaction_errors: a bool for whether we should get errors
                when transactions try to commit

        Returns: an instance of MockGraph
        """

        mock_graph = MockGraph(transaction_errors=transaction_errors)
        mock_graph_class.return_value = mock_graph

        mock_node_selector = MockNodeSelector(mock_graph)
        mock_selector_class.return_value = mock_node_selector
        return mock_graph

    def assertCourseDump(self, mock_graph, number_of_courses, number_commits, number_rollbacks):
        """
        Asserts that we have the expected number of courses, commits, and
        rollbacks after we dump the modulestore to neo4j
        Args:
            mock_graph: a MockGraph backend
            number_of_courses: number of courses we expect to find
            number_commits: number of commits we expect against the graph
            number_rollbacks: number of commit rollbacks we expect
        """
        courses = set([node['course_key'] for node in mock_graph.nodes])
        self.assertEqual(len(courses), number_of_courses)
        self.assertEqual(mock_graph.number_commits, number_commits)
        self.assertEqual(mock_graph.number_rollbacks, number_rollbacks)


@ddt.ddt
class TestDumpToNeo4jCommand(TestDumpToNeo4jCommandBase):
    """
    Tests for the dump to neo4j management command
    """

    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.NodeSelector')
    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.Graph')
    @ddt.data(1, 2)
    def test_dump_specific_courses(self, number_of_courses, mock_graph_class, mock_selector_class):
        """
        Test that you can specify which courses you want to dump.
        """
        mock_graph = self.setup_mock_graph(mock_selector_class, mock_graph_class)

        call_command(
            'dump_to_neo4j',
            courses=self.course_strings[:number_of_courses],
            host='mock_host',
            http_port=7474,
            user='mock_user',
            password='mock_password',
        )

        self.assertCourseDump(
            mock_graph,
            number_of_courses=number_of_courses,
            number_commits=number_of_courses,
            number_rollbacks=0
        )

    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.NodeSelector')
    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.Graph')
    def test_dump_skip_course(self, mock_graph_class, mock_selector_class):
        """
        Test that you can skip courses.
        """
        mock_graph = self.setup_mock_graph(
            mock_selector_class, mock_graph_class
        )

        call_command(
            'dump_to_neo4j',
            skip=self.course_strings[:1],
            host='mock_host',
            http_port=7474,
            user='mock_user',
            password='mock_password',
        )

        self.assertCourseDump(
            mock_graph,
            number_of_courses=1,
            number_commits=1,
            number_rollbacks=0,
        )

    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.NodeSelector')
    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.Graph')
    def test_dump_skip_beats_specifying(self, mock_graph_class, mock_selector_class):
        """
        Test that if you skip and specify the same course, you'll skip it.
        """
        mock_graph = self.setup_mock_graph(
            mock_selector_class, mock_graph_class
        )

        call_command(
            'dump_to_neo4j',
            skip=self.course_strings[:1],
            courses=self.course_strings[:1],
            host='mock_host',
            http_port=7474,
            user='mock_user',
            password='mock_password',
        )

        self.assertCourseDump(
            mock_graph,
            number_of_courses=0,
            number_commits=0,
            number_rollbacks=0,
        )

    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.NodeSelector')
    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.Graph')
    def test_dump_all_courses(self, mock_graph_class, mock_selector_class):
        """
        Test if you don't specify which courses to dump, then you'll dump
        all of them.
        """
        mock_graph = self.setup_mock_graph(
            mock_selector_class, mock_graph_class
        )

        call_command(
            'dump_to_neo4j',
            host='mock_host',
            http_port=7474,
            user='mock_user',
            password='mock_password'
        )

        self.assertCourseDump(
            mock_graph,
            number_of_courses=2,
            number_commits=2,
            number_rollbacks=0,
        )


@ddt.ddt
class TestModuleStoreSerializer(TestDumpToNeo4jCommandBase):
    """
    Tests for the ModuleStoreSerializer
    """
    @classmethod
    def setUpClass(cls):
        """Any ModuleStore course/content operations can go here."""
        super(TestModuleStoreSerializer, cls).setUpClass()
        cls.mss = ModuleStoreSerializer()

    def test_serialize_item(self):
        """
        Tests the serialize_item method.
        """
        fields, label = self.mss.serialize_item(self.course)
        self.assertEqual(label, "course")
        self.assertIn("edited_on", fields.keys())
        self.assertIn("display_name", fields.keys())
        self.assertIn("org", fields.keys())
        self.assertIn("course", fields.keys())
        self.assertIn("run", fields.keys())
        self.assertIn("course_key", fields.keys())
        self.assertIn("location", fields.keys())
        self.assertIn("block_type", fields.keys())
        self.assertIn("detached", fields.keys())
        self.assertNotIn("checklist", fields.keys())

    def test_serialize_course(self):
        """
        Tests the serialize_course method.
        """
        nodes, relationships = self.mss.serialize_course(self.course.id)
        self.assertEqual(len(nodes), 9)
        self.assertEqual(len(relationships), 7)

    @ddt.data(
        (1, 1),
        (object, "<type 'object'>"),
        (1.5, 1.5),
        ("úñîçø∂é", "úñîçø∂é"),
        (b"plain string", b"plain string"),
        (True, True),
        (None, "None"),
        ((1,), "(1,)"),
        # list of elements should be coerced into a list of the
        # string representations of those elements
        ([object, object], ["<type 'object'>", "<type 'object'>"])
    )
    @ddt.unpack
    def test_coerce_types(self, original_value, coerced_expected):
        """
        Tests the coerce_types helper
        """
        coerced_value = self.mss.coerce_types(original_value)
        self.assertEqual(coerced_value, coerced_expected)

    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.NodeSelector')
    def test_dump_to_neo4j(self, mock_selector_class):
        """
        Tests the dump_to_neo4j method works against a mock
        py2neo Graph
        """
        mock_graph = MockGraph()
        mock_selector_class.return_value = MockNodeSelector(mock_graph)

        successful, unsuccessful = self.mss.dump_courses_to_neo4j(mock_graph)

        self.assertCourseDump(
            mock_graph,
            number_of_courses=2,
            number_commits=2,
            number_rollbacks=0,
        )

        # 9 nodes + 7 relationships from the first course
        # 2 nodes and no relationships from the second

        self.assertEqual(len(mock_graph.nodes), 11)

        self.assertEqual(len(unsuccessful), 0)
        self.assertItemsEqual(successful, self.course_strings)

    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.NodeSelector')
    def test_dump_to_neo4j_rollback(self, mock_selector_class):
        """
        Tests that the the dump_to_neo4j method handles the case where there's
        an exception trying to write to the neo4j database.
        """
        mock_graph = MockGraph(transaction_errors=True)
        mock_selector_class.return_value = MockNodeSelector(mock_graph)

        successful, unsuccessful = self.mss.dump_courses_to_neo4j(mock_graph)

        self.assertCourseDump(
            mock_graph,
            number_of_courses=0,
            number_commits=0,
            number_rollbacks=2,
        )

        self.assertEqual(len(successful), 0)
        self.assertItemsEqual(unsuccessful, self.course_strings)

    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.NodeSelector')
    @ddt.data((True, 2), (False, 0))
    @ddt.unpack
    def test_dump_to_neo4j_cache(self, override_cache, expected_number_courses, mock_selector_class):
        """
        Tests the caching mechanism and override to make sure we only publish
        recently updated courses.
        """
        mock_graph = MockGraph()
        mock_selector_class.return_value = MockNodeSelector(mock_graph)

        # run once to warm the cache
        self.mss.dump_courses_to_neo4j(
            mock_graph, override_cache=override_cache
        )

        # when run the second time, only dump courses if the cache override
        # is enabled
        successful, unsuccessful = self.mss.dump_courses_to_neo4j(
            mock_graph, override_cache=override_cache
        )
        self.assertEqual(len(successful + unsuccessful), expected_number_courses)

    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.NodeSelector')
    def test_dump_to_neo4j_published(self, mock_selector_class):
        """
        Tests that we only dump those courses that have been published after
        the last time the command was been run.
        """
        mock_graph = MockGraph()
        mock_selector_class.return_value = MockNodeSelector(mock_graph)

        # run once to warm the cache
        successful, unsuccessful = self.mss.dump_courses_to_neo4j(mock_graph)
        self.assertEqual(len(successful + unsuccessful), len(self.course_strings))

        # simulate one of the courses being published
        listen_for_course_publish(None, self.course.id)

        # make sure only the published course was dumped
        successful, unsuccessful = self.mss.dump_courses_to_neo4j(mock_graph)
        self.assertEqual(len(unsuccessful), 0)
        self.assertEqual(len(successful), 1)
        self.assertEqual(successful[0], unicode(self.course.id))

    @ddt.data(
        (six.text_type(datetime(2016, 3, 30)), six.text_type(datetime(2016, 3, 31)), True),
        (six.text_type(datetime(2016, 3, 31)), six.text_type(datetime(2016, 3, 30)), False),
        (six.text_type(datetime(2016, 3, 31)), None, False),
        (None, six.text_type(datetime(2016, 3, 30)), True),
        (None, None, True),
    )
    @ddt.unpack
    def test_should_dump_course(self, last_command_run, last_course_published, should_dump):
        """
        Tests whether a course should be dumped given the last time it was
        dumped and the last time it was published.
        """
        mss = ModuleStoreSerializer()
        mss.get_command_last_run = lambda course_key, graph: last_command_run
        mss.get_course_last_published = lambda course_key: last_course_published
        mock_course_key = mock.Mock
        mock_graph = mock.Mock()
        self.assertEqual(
            mss.should_dump_course(mock_course_key, mock_graph),
            should_dump,
        )
