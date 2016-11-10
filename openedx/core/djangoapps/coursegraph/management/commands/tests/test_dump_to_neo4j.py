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
from openedx.core.djangoapps.coursegraph.signals import _listen_for_course_publish


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


@ddt.ddt
class TestDumpToNeo4jCommand(TestDumpToNeo4jCommandBase):
    """
    Tests for the dump to neo4j management command
    """

    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.Graph')
    @ddt.data(1, 2)
    def test_dump_specific_courses(self, number_of_courses, mock_graph_class):
        """
        Test that you can specify which courses you want to dump.
        """
        mock_graph = mock_graph_class.return_value
        mock_transaction = mock.Mock()
        mock_graph.begin.return_value = mock_transaction

        call_command(
            'dump_to_neo4j',
            courses=self.course_strings[:number_of_courses],
            host='mock_host',
            http_port=7474,
            user='mock_user',
            password='mock_password',
        )

        self.assertEqual(mock_graph.begin.call_count, number_of_courses)
        self.assertEqual(mock_transaction.commit.call_count, number_of_courses)
        self.assertEqual(mock_transaction.commit.rollback.call_count, 0)

    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.Graph')
    def test_dump_skip_course(self, mock_graph_class):
        """
        Test that you can skip courses.
        """
        mock_graph = mock_graph_class.return_value
        mock_transaction = mock.Mock()
        mock_graph.begin.return_value = mock_transaction

        call_command(
            'dump_to_neo4j',
            skip=self.course_strings[:1],
            host='mock_host',
            http_port=7474,
            user='mock_user',
            password='mock_password',
        )

        self.assertEqual(mock_graph.begin.call_count, 1)
        self.assertEqual(mock_transaction.commit.call_count, 1)
        self.assertEqual(mock_transaction.commit.rollback.call_count, 0)

    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.Graph')
    def test_dump_skip_beats_specifying(self, mock_graph_class):
        """
        Test that if you skip and specify the same course, you'll skip it.
        """
        mock_graph = mock_graph_class.return_value
        mock_transaction = mock.Mock()
        mock_graph.begin.return_value = mock_transaction

        call_command(
            'dump_to_neo4j',
            skip=self.course_strings[:1],
            courses=self.course_strings[:1],
            host='mock_host',
            http_port=7474,
            user='mock_user',
            password='mock_password',
        )

        self.assertEqual(mock_graph.begin.call_count, 0)
        self.assertEqual(mock_transaction.commit.call_count, 0)
        self.assertEqual(mock_transaction.commit.rollback.call_count, 0)

    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.Graph')
    def test_dump_all_courses(self, mock_graph_class):
        """
        Test if you don't specify which courses to dump, then you'll dump
        all of them.
        """
        mock_graph = mock_graph_class.return_value
        mock_transaction = mock.Mock()
        mock_graph.begin.return_value = mock_transaction

        call_command(
            'dump_to_neo4j',
            host='mock_host',
            http_port=7474,
            user='mock_user',
            password='mock_password',
        )

        self.assertEqual(mock_graph.begin.call_count, 2)
        self.assertEqual(mock_transaction.commit.call_count, 2)
        self.assertEqual(mock_transaction.commit.rollback.call_count, 0)


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
        self.assertNotIn("checklist", fields.keys())

    def test_serialize_course(self):
        """
        Tests the serialize_course method.
        """
        nodes, relationships = self.mss.serialize_course(
            self.course.id
        )
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

    def test_dump_to_neo4j(self):
        """
        Tests the dump_to_neo4j method works against a mock
        py2neo Graph
        """
        mock_graph = mock.Mock()
        mock_transaction = mock.Mock()
        mock_graph.begin.return_value = mock_transaction

        successful, unsuccessful = self.mss.dump_courses_to_neo4j(mock_graph)

        self.assertEqual(mock_graph.begin.call_count, 2)
        self.assertEqual(mock_transaction.commit.call_count, 2)
        self.assertEqual(mock_transaction.rollback.call_count, 0)

        # 7 nodes + 9 relationships from the first course
        # 2 nodes and no relationships from the second
        self.assertEqual(mock_transaction.create.call_count, 18)
        self.assertEqual(mock_transaction.run.call_count, 2)

        self.assertEqual(len(unsuccessful), 0)
        self.assertItemsEqual(successful, self.course_strings)

    def test_dump_to_neo4j_rollback(self):
        """
        Tests that the the dump_to_neo4j method handles the case where there's
        an exception trying to write to the neo4j database.
        """
        mock_graph = mock.Mock()
        mock_transaction = mock.Mock()
        mock_graph.begin.return_value = mock_transaction
        mock_transaction.run.side_effect = ValueError('Something went wrong!')

        successful, unsuccessful = self.mss.dump_courses_to_neo4j(mock_graph)

        self.assertEqual(mock_graph.begin.call_count, 2)
        self.assertEqual(mock_transaction.commit.call_count, 0)
        self.assertEqual(mock_transaction.rollback.call_count, 2)

        self.assertEqual(len(successful), 0)
        self.assertItemsEqual(unsuccessful, self.course_strings)

    @ddt.data(
        (True, 2),
        (False, 0),
    )
    @ddt.unpack
    def test_dump_to_neo4j_cache(self, override_cache, expected_number_courses):
        """
        Tests the caching mechanism and override to make sure we only publish
        recently updated courses.
        """
        mock_graph = mock.Mock()

        # run once to warm the cache
        successful, unsuccessful = self.mss.dump_courses_to_neo4j(mock_graph)
        self.assertEqual(len(successful + unsuccessful), len(self.course_strings))

        # when run the second time, only dump courses if the cache override
        # is enabled
        successful, unsuccessful = self.mss.dump_courses_to_neo4j(
            mock_graph, override_cache=override_cache
        )
        self.assertEqual(len(successful + unsuccessful), expected_number_courses)

    def test_dump_to_neo4j_published(self):
        """
        Tests that we only dump those courses that have been published after
        the last time the command was been run.
        """
        mock_graph = mock.Mock()

        # run once to warm the cache
        successful, unsuccessful = self.mss.dump_courses_to_neo4j(mock_graph)
        self.assertEqual(len(successful + unsuccessful), len(self.course_strings))

        # simulate one of the courses being published
        _listen_for_course_publish(None, self.course.id)

        # make sure only the published course was dumped
        successful, unsuccessful = self.mss.dump_courses_to_neo4j(mock_graph)
        self.assertEqual(len(unsuccessful), 0)
        self.assertEqual(len(successful), 1)
        self.assertEqual(successful[0], unicode(self.course.id))

    @ddt.data(
        (datetime(2016, 3, 30), datetime(2016, 3, 31), True),
        (datetime(2016, 3, 31), datetime(2016, 3, 30), False),
        (datetime(2016, 3, 31), None, False),
        (None, datetime(2016, 3, 30), True),
        (None, None, True),
    )
    @ddt.unpack
    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.COMMAND_LAST_RUN_CACHE')
    @mock.patch('openedx.core.djangoapps.coursegraph.management.commands.dump_to_neo4j.COURSE_LAST_PUBLISHED_CACHE')
    def test_should_dump_course(
            self,
            last_command_run,
            last_course_published,
            should_dump,
            mock_course_last_published_cache,
            mock_command_last_run_cache,
    ):
        """
        Tests whether a course should be dumped given the last time it was
        dumped and the last time it was published.
        """
        mock_command_last_run_cache.get.return_value = last_command_run
        mock_course_last_published_cache.get.return_value = last_course_published
        mock_course_key = mock.Mock
        self.assertEqual(
            self.mss.should_dump_course(mock_course_key),
            should_dump
        )
