"""
Tests for the dump_to_neo4j management command.
"""


from datetime import datetime

from unittest import mock
import ddt
from django.core.management import call_command
from django.test.utils import override_settings
from edx_toggles.toggles.testutils import override_waffle_switch
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory

import openedx.core.djangoapps.content.block_structure.config as block_structure_config
from openedx.core.djangoapps.content.block_structure.signals import update_block_structure_on_course_publish
from cms.djangoapps.coursegraph.management.commands.dump_to_neo4j import ModuleStoreSerializer
from cms.djangoapps.coursegraph.management.commands.tests.utils import MockGraph, MockNodeMatcher
from cms.djangoapps.coursegraph.tasks import (
    coerce_types,
    serialize_course,
    serialize_item,
    should_dump_course,
    strip_branch_and_version
)
from openedx.core.djangolib.testing.utils import skip_unless_lms


class TestDumpToNeo4jCommandBase(SharedModuleStoreTestCase):
    """
    Base class for the test suites in this file. Sets up a couple courses.
    """
    @classmethod
    def setUpClass(cls):
        r"""
        Creates two courses; one that's just a course block, and one that
        looks like:
                        course
                           |
                        chapter
                           |
                        sequential
                           |
                        vertical
                        / |  \  \
                       /  |   \  ----------
                      /   |    \           \
                     /    |     ---         \
                    /     |        \         \
                html -> problem -> video -> video2

        The side-pointing arrows (->) are PRECEDES relationships; the more
        vertical lines are PARENT_OF relationships.

        The vertical in this course and the first video have the same
        display_name, so that their block_ids are the same. This is to
        test for a bug where xblocks with the same block_ids (but different
        locations) pointed to themselves erroneously.
        """
        super().setUpClass()
        cls.course = CourseFactory.create()
        cls.chapter = BlockFactory.create(parent=cls.course, category='chapter')
        cls.sequential = BlockFactory.create(parent=cls.chapter, category='sequential')
        cls.vertical = BlockFactory.create(parent=cls.sequential, category='vertical', display_name='subject')
        cls.html = BlockFactory.create(parent=cls.vertical, category='html')
        cls.problem = BlockFactory.create(parent=cls.vertical, category='problem')
        cls.video = BlockFactory.create(parent=cls.vertical, category='video', display_name='subject')
        cls.video2 = BlockFactory.create(parent=cls.vertical, category='video')

        cls.course2 = CourseFactory.create()

        cls.course_strings = [str(cls.course.id), str(cls.course2.id)]

    @staticmethod
    def setup_mock_graph(mock_matcher_class, mock_graph_class, transaction_errors=False):
        """
        Replaces the py2neo Graph object with a MockGraph; similarly replaces
        NodeMatcher with MockNodeMatcher.

        Arguments:
            mock_matcher_class: a mocked NodeMatcher class
            mock_graph_class: a mocked Graph class
            transaction_errors: a bool for whether we should get errors
                when transactions try to commit

        Returns: an instance of MockGraph
        """

        mock_graph = MockGraph(transaction_errors=transaction_errors)
        mock_graph_class.return_value = mock_graph

        mock_node_matcher = MockNodeMatcher(mock_graph)
        mock_matcher_class.return_value = mock_node_matcher
        return mock_graph

    def assertCourseDump(self, mock_graph, number_of_courses, number_commits, number_rollbacks):
        """
        Asserts that we have the expected number of courses, commits, and
        rollbacks after we dump the modulestore to neo4j
        Arguments:
            mock_graph: a MockGraph backend
            number_of_courses: number of courses we expect to find
            number_commits: number of commits we expect against the graph
            number_rollbacks: number of commit rollbacks we expect
        """
        courses = {node['course_key'] for node in mock_graph.nodes}
        assert len(courses) == number_of_courses
        assert mock_graph.number_commits == number_commits
        assert mock_graph.number_rollbacks == number_rollbacks


@ddt.ddt
class TestDumpToNeo4jCommand(TestDumpToNeo4jCommandBase):
    """
    Tests for the dump to neo4j management command
    """

    @mock.patch('cms.djangoapps.coursegraph.tasks.NodeMatcher')
    @mock.patch('cms.djangoapps.coursegraph.tasks.Graph')
    @ddt.data(1, 2)
    def test_dump_specific_courses(self, number_of_courses, mock_graph_class, mock_matcher_class):
        """
        Test that you can specify which courses you want to dump.
        """
        mock_graph = self.setup_mock_graph(mock_matcher_class, mock_graph_class)

        call_command(
            'dump_to_neo4j',
            courses=self.course_strings[:number_of_courses],
            host='mock_host',
            port=7687,
            user='mock_user',
            password='mock_password',
        )

        self.assertCourseDump(
            mock_graph,
            number_of_courses=number_of_courses,
            number_commits=number_of_courses,
            number_rollbacks=0
        )

    @mock.patch('cms.djangoapps.coursegraph.tasks.NodeMatcher')
    @mock.patch('cms.djangoapps.coursegraph.tasks.Graph')
    def test_dump_skip_course(self, mock_graph_class, mock_matcher_class):
        """
        Test that you can skip courses.
        """
        mock_graph = self.setup_mock_graph(
            mock_matcher_class, mock_graph_class
        )

        call_command(
            'dump_to_neo4j',
            skip=self.course_strings[:1],
            host='mock_host',
            port=7687,
            user='mock_user',
            password='mock_password',
        )

        self.assertCourseDump(
            mock_graph,
            number_of_courses=1,
            number_commits=1,
            number_rollbacks=0,
        )

    @mock.patch('cms.djangoapps.coursegraph.tasks.NodeMatcher')
    @mock.patch('cms.djangoapps.coursegraph.tasks.Graph')
    def test_dump_skip_beats_specifying(self, mock_graph_class, mock_matcher_class):
        """
        Test that if you skip and specify the same course, you'll skip it.
        """
        mock_graph = self.setup_mock_graph(
            mock_matcher_class, mock_graph_class
        )

        call_command(
            'dump_to_neo4j',
            skip=self.course_strings[:1],
            courses=self.course_strings[:1],
            host='mock_host',
            port=7687,
            user='mock_user',
            password='mock_password',
        )

        self.assertCourseDump(
            mock_graph,
            number_of_courses=0,
            number_commits=0,
            number_rollbacks=0,
        )

    @mock.patch('cms.djangoapps.coursegraph.tasks.NodeMatcher')
    @mock.patch('cms.djangoapps.coursegraph.tasks.Graph')
    def test_dump_all_courses(self, mock_graph_class, mock_matcher_class):
        """
        Test if you don't specify which courses to dump, then you'll dump
        all of them.
        """
        mock_graph = self.setup_mock_graph(
            mock_matcher_class, mock_graph_class
        )

        call_command(
            'dump_to_neo4j',
            host='mock_host',
            port=7687,
            user='mock_user',
            password='mock_password'
        )

        self.assertCourseDump(
            mock_graph,
            number_of_courses=2,
            number_commits=2,
            number_rollbacks=0,
        )

    @mock.patch('cms.djangoapps.coursegraph.tasks.NodeMatcher')
    @mock.patch('cms.djangoapps.coursegraph.tasks.Graph', autospec=True)
    @override_settings(
        COURSEGRAPH_CONNECTION=dict(
            protocol='bolt',
            host='coursegraph.example.edu',
            port=7777,
            secure=True,
            user="neo4j",
            password="default-password",
        )
    )
    def test_dump_to_neo4j_connection_defaults(self, mock_graph_class, mock_matcher_class):
        """
        Test that user can override individual settings.COURSEGRAPH_CONNECTION parameters
        by passing them to `dump_to_neo4j`, whilst falling back to the ones that they
        don't override.
        """
        self.setup_mock_graph(
            mock_matcher_class, mock_graph_class
        )
        call_command(
            'dump_to_neo4j',
            courses=self.course_strings[:1],
            port=7788,
            secure=False,
            password="overridden-password",
        )
        assert mock_graph_class.call_args.args == ()
        assert mock_graph_class.call_args.kwargs == dict(

            # From settings:
            protocol='bolt',
            host='coursegraph.example.edu',
            user="neo4j",

            # Overriden by command:
            port=7788,
            secure=False,
            password="overridden-password",
        )


class SomeThing:
    """Just to test the stringification of an object."""
    def __str__(self):
        return "<SomeThing>"


@skip_unless_lms
@ddt.ddt
class TestModuleStoreSerializer(TestDumpToNeo4jCommandBase):
    """
    Tests for the ModuleStoreSerializer
    """
    @classmethod
    def setUpClass(cls):
        """Any ModuleStore course/content operations can go here."""
        super().setUpClass()
        cls.mss = ModuleStoreSerializer.create()

    def test_serialize_item(self):
        """
        Tests the serialize_item method.
        """
        fields, label = serialize_item(self.course)
        assert label == 'course'
        assert 'edited_on' in list(fields.keys())
        assert 'display_name' in list(fields.keys())
        assert 'org' in list(fields.keys())
        assert 'course' in list(fields.keys())
        assert 'run' in list(fields.keys())
        assert 'course_key' in list(fields.keys())
        assert 'location' in list(fields.keys())
        assert 'block_type' in list(fields.keys())
        assert 'detached' in list(fields.keys())
        assert 'checklist' not in list(fields.keys())

    def test_serialize_course(self):
        """
        Tests the serialize_course method.
        """
        nodes, relationships = serialize_course(self.course.id)
        assert len(nodes) == 9
        # the course has 7 "PARENT_OF" relationships and 3 "PRECEDES"
        assert len(relationships) == 10

    def test_strip_version_and_branch(self):
        """
        Tests that the _strip_version_and_branch function strips the version
        and branch from a location
        """
        location = self.course.id.make_usage_key(
            'test_block_type', 'test_block_id'
        ).for_branch(
            'test_branch'
        ).for_version(b'test_version')

        assert location.branch is not None
        assert location.version_guid is not None

        stripped_location = strip_branch_and_version(location)

        assert stripped_location.branch is None
        assert stripped_location.version_guid is None

    @staticmethod
    def _extract_relationship_pairs(relationships, relationship_type):
        """
        Extracts a list of XBlock location tuples from a list of Relationships.

        Arguments:
            relationships: list of py2neo `Relationship` objects
            relationship_type: the type of relationship to filter `relationships`
              by.
        Returns:
            List of tuples of the locations of of the relationships'
              constituent nodes.
        """
        relationship_pairs = [
            (rel.start_node["location"], rel.end_node["location"])
            for rel in relationships if type(rel).__name__ == relationship_type
        ]
        return relationship_pairs

    @staticmethod
    def _extract_location_pair(xblock1, xblock2):
        """
        Returns a tuple of locations from two XBlocks.

        Arguments:
            xblock1: an xblock
            xblock2: also an xblock

        Returns:
            A tuple of the string representations of those XBlocks' locations.
        """
        return (str(xblock1.location), str(xblock2.location))

    def assertBlockPairIsRelationship(self, xblock1, xblock2, relationships, relationship_type):
        """
        Helper assertion that a pair of xblocks have a certain kind of
        relationship with one another.
        """
        relationship_pairs = self._extract_relationship_pairs(relationships, relationship_type)
        location_pair = self._extract_location_pair(xblock1, xblock2)
        assert location_pair in relationship_pairs

    def assertBlockPairIsNotRelationship(self, xblock1, xblock2, relationships, relationship_type):
        """
        The opposite of `assertBlockPairIsRelationship`: asserts that a pair
        of xblocks do NOT have a certain kind of relationship.
        """
        relationship_pairs = self._extract_relationship_pairs(relationships, relationship_type)
        location_pair = self._extract_location_pair(xblock1, xblock2)
        assert location_pair not in relationship_pairs

    def test_precedes_relationship(self):
        """
        Tests that two nodes that should have a precedes relationship have it.
        """
        __, relationships = serialize_course(self.course.id)
        self.assertBlockPairIsRelationship(self.video, self.video2, relationships, "PRECEDES")
        self.assertBlockPairIsNotRelationship(self.video2, self.video, relationships, "PRECEDES")
        self.assertBlockPairIsNotRelationship(self.vertical, self.video, relationships, "PRECEDES")
        self.assertBlockPairIsNotRelationship(self.html, self.video, relationships, "PRECEDES")

    def test_parent_relationship(self):
        """
        Test that two nodes that should have a parent_of relationship have it.
        """
        __, relationships = serialize_course(self.course.id)
        self.assertBlockPairIsRelationship(self.vertical, self.video, relationships, "PARENT_OF")
        self.assertBlockPairIsRelationship(self.vertical, self.html, relationships, "PARENT_OF")
        self.assertBlockPairIsRelationship(self.course, self.chapter, relationships, "PARENT_OF")
        self.assertBlockPairIsNotRelationship(self.course, self.video, relationships, "PARENT_OF")
        self.assertBlockPairIsNotRelationship(self.video, self.vertical, relationships, "PARENT_OF")
        self.assertBlockPairIsNotRelationship(self.video, self.html, relationships, "PARENT_OF")

    def test_nodes_have_indices(self):
        """
        Test that we add index values on nodes
        """
        nodes, relationships = serialize_course(self.course.id)  # lint-amnesty, pylint: disable=unused-variable

        # the html node should have 0 index, and the problem should have 1
        html_nodes = [node for node in nodes if node['block_type'] == 'html']
        assert len(html_nodes) == 1
        problem_nodes = [node for node in nodes if node['block_type'] == 'problem']
        assert len(problem_nodes) == 1
        html_node = html_nodes[0]
        problem_node = problem_nodes[0]

        assert html_node['index'] == 0
        assert problem_node['index'] == 1

    @ddt.data(
        (1, 1),
        (SomeThing(), "<SomeThing>"),
        (1.5, 1.5),
        ("úñîçø∂é", "úñîçø∂é"),
        (b"plain string", b"plain string"),
        (True, True),
        (None, "None"),
        ((1,), "(1,)"),
        # list of elements should be coerced into a list of the
        # string representations of those elements
        ([SomeThing(), SomeThing()], ["<SomeThing>", "<SomeThing>"]),
        ([1, 2], ["1", "2"]),
    )
    @ddt.unpack
    def test_coerce_types(self, original_value, coerced_expected):
        """
        Tests the coerce_types helper
        """
        coerced_value = coerce_types(original_value)
        assert coerced_value == coerced_expected

    @mock.patch('cms.djangoapps.coursegraph.tasks.NodeMatcher')
    @mock.patch('cms.djangoapps.coursegraph.tasks.authenticate_and_create_graph')
    def test_dump_to_neo4j(self, mock_graph_constructor, mock_matcher_class):
        """
        Tests the dump_to_neo4j method works against a mock
        py2neo Graph
        """
        mock_graph = MockGraph()
        mock_graph_constructor.return_value = mock_graph
        mock_matcher_class.return_value = MockNodeMatcher(mock_graph)
        # mocking is thorwing error in kombu serialzier and its not require here any more.
        credentials = {}

        submitted, skipped = self.mss.dump_courses_to_neo4j(credentials)  # lint-amnesty, pylint: disable=unused-variable

        self.assertCourseDump(
            mock_graph,
            number_of_courses=2,
            number_commits=2,
            number_rollbacks=0,
        )

        # 9 nodes + 7 relationships from the first course
        # 2 nodes and no relationships from the second

        assert len(mock_graph.nodes) == 11
        self.assertCountEqual(submitted, self.course_strings)

    @mock.patch('cms.djangoapps.coursegraph.tasks.NodeMatcher')
    @mock.patch('cms.djangoapps.coursegraph.tasks.authenticate_and_create_graph')
    def test_dump_to_neo4j_rollback(self, mock_graph_constructor, mock_matcher_class):
        """
        Tests that the the dump_to_neo4j method handles the case where there's
        an exception trying to write to the neo4j database.
        """
        mock_graph = MockGraph(transaction_errors=True)
        mock_graph_constructor.return_value = mock_graph
        mock_matcher_class.return_value = MockNodeMatcher(mock_graph)
        # mocking is thorwing error in kombu serialzier and its not require here any more.
        credentials = {}

        submitted, skipped = self.mss.dump_courses_to_neo4j(credentials)  # lint-amnesty, pylint: disable=unused-variable

        self.assertCourseDump(
            mock_graph,
            number_of_courses=0,
            number_commits=0,
            number_rollbacks=2,
        )

        self.assertCountEqual(submitted, self.course_strings)

    @mock.patch('cms.djangoapps.coursegraph.tasks.NodeMatcher')
    @mock.patch('cms.djangoapps.coursegraph.tasks.authenticate_and_create_graph')
    @ddt.data((True, 2), (False, 0))
    @ddt.unpack
    def test_dump_to_neo4j_cache(
        self,
        override_cache,
        expected_number_courses,
        mock_graph_constructor,
        mock_matcher_class,
    ):
        """
        Tests the caching mechanism and override to make sure we only publish
        recently updated courses.
        """
        mock_graph = MockGraph()
        mock_graph_constructor.return_value = mock_graph
        mock_matcher_class.return_value = MockNodeMatcher(mock_graph)
        # mocking is thorwing error in kombu serialzier and its not require here any more.
        credentials = {}

        # run once to warm the cache
        self.mss.dump_courses_to_neo4j(
            credentials, override_cache=override_cache
        )

        # when run the second time, only dump courses if the cache override
        # is enabled
        submitted, __ = self.mss.dump_courses_to_neo4j(
            credentials, override_cache=override_cache
        )
        assert len(submitted) == expected_number_courses

    @mock.patch('cms.djangoapps.coursegraph.tasks.NodeMatcher')
    @mock.patch('cms.djangoapps.coursegraph.tasks.authenticate_and_create_graph')
    def test_dump_to_neo4j_published(self, mock_graph_constructor, mock_matcher_class):
        """
        Tests that we only dump those courses that have been published after
        the last time the command was been run.
        """
        mock_graph = MockGraph()
        mock_graph_constructor.return_value = mock_graph
        mock_matcher_class.return_value = MockNodeMatcher(mock_graph)
        # mocking is thorwing error in kombu serialzier and its not require here any more.
        credentials = {}

        # run once to warm the cache
        submitted, skipped = self.mss.dump_courses_to_neo4j(credentials)  # lint-amnesty, pylint: disable=unused-variable
        assert len(submitted) == len(self.course_strings)

        # simulate one of the courses being published
        with override_waffle_switch(block_structure_config.STORAGE_BACKING_FOR_CACHE, True):
            update_block_structure_on_course_publish(None, self.course.id)

        # make sure only the published course was dumped
        submitted, __ = self.mss.dump_courses_to_neo4j(credentials)
        assert len(submitted) == 1
        assert submitted[0] == str(self.course.id)

    @mock.patch('cms.djangoapps.coursegraph.tasks.get_course_last_published')
    @mock.patch('cms.djangoapps.coursegraph.tasks.get_command_last_run')
    @ddt.data(
        (
            str(datetime(2016, 3, 30)), str(datetime(2016, 3, 31)),
            (True, (
                'course has been published since last neo4j update time - '
                'update date 2016-03-30 00:00:00 < published date 2016-03-31 00:00:00'
            ))
        ),
        (
            str(datetime(2016, 3, 31)), str(datetime(2016, 3, 30)),
            (False, None)
        ),
        (
            str(datetime(2016, 3, 31)), None,
            (False, None)
        ),
        (
            None, str(datetime(2016, 3, 30)),
            (True, 'no record of the last neo4j update time for the course')
        ),
        (
            None, None,
            (True, 'no record of the last neo4j update time for the course')
        ),
    )
    @ddt.unpack
    def test_should_dump_course(
        self,
        last_command_run,
        last_course_published,
        should_dump,
        mock_get_command_last_run,
        mock_get_course_last_published,
    ):
        """
        Tests whether a course should be dumped given the last time it was
        dumped and the last time it was published.
        """
        mock_get_command_last_run.return_value = last_command_run
        mock_get_course_last_published.return_value = last_course_published
        mock_course_key = mock.Mock()
        mock_graph = mock.Mock()
        assert should_dump_course(mock_course_key, mock_graph) == should_dump
