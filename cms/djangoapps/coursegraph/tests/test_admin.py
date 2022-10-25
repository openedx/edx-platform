"""
Shallow tests for CourseGraph dump-queueing Django admin interface.

See ..management.commands.tests.test_dump_to_neo4j for more comprehensive
tests of dump_course_to_neo4j.
"""

from unittest import mock

import py2neo
from django.test import TestCase
from django.test.utils import override_settings
from freezegun import freeze_time

from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from .. import admin, tasks


_coursegraph_connection = {
    "protocol": "bolt",
    "secure": True,
    "host": "example.edu",
    "port": 7687,
    "user": "neo4j",
    "password": "fake-coursegraph-password",
}

_configure_coursegraph_connection = override_settings(
    COURSEGRAPH_CONNECTION=_coursegraph_connection,
)

_patch_log_exception = mock.patch.object(
    admin.log, 'exception', autospec=True
)

_patch_apply_dump_task = mock.patch.object(
    tasks.dump_course_to_neo4j, 'apply_async'
)

_pretend_last_course_dump_was_may_2020 = mock.patch.object(
    tasks,
    'get_command_last_run',
    new=(lambda _key, _graph: "2020-05-01"),
)

_patch_neo4j_graph = mock.patch.object(
    tasks, 'Graph', autospec=True
)

_make_neo4j_graph_raise = mock.patch.object(
    tasks, 'Graph', side_effect=py2neo.ConnectionUnavailable(
        'we failed to connect or something!'
    )
)


class CourseGraphAdminActionsTestCase(TestCase):
    """
    Test CourseGraph Django admin actions.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Make course overviews with varying modification dates.
        """
        super().setUpTestData()
        cls.course_updated_in_april = CourseOverviewFactory(run='april_update')
        cls.course_updated_in_june = CourseOverviewFactory(run='june_update')
        cls.course_updated_in_july = CourseOverviewFactory(run='july_update')
        cls.course_updated_in_august = CourseOverviewFactory(run='august_update')

        # For each course overview, make an arbitrary update and then save()
        # so that its `.modified` date is set.
        with freeze_time("2020-04-01"):
            cls.course_updated_in_april.marketing_url = "https://example.org"
            cls.course_updated_in_april.save()
        with freeze_time("2020-06-01"):
            cls.course_updated_in_june.marketing_url = "https://example.org"
            cls.course_updated_in_june.save()
        with freeze_time("2020-07-01"):
            cls.course_updated_in_july.marketing_url = "https://example.org"
            cls.course_updated_in_july.save()
        with freeze_time("2020-08-01"):
            cls.course_updated_in_august.marketing_url = "https://example.org"
            cls.course_updated_in_august.save()

    @_configure_coursegraph_connection
    @_pretend_last_course_dump_was_may_2020
    @_patch_neo4j_graph
    @_patch_apply_dump_task
    @_patch_log_exception
    def test_dump_courses(self, mock_log_exception, mock_apply_dump_task, mock_neo4j_graph):
        """
        Test that dump_courses admin action dumps requested courses iff they have
        been modified since the last dump to coursegraph.
        """
        modeladmin_mock = mock.MagicMock()

        # Request all courses except the August-updated one
        requested_course_keys = {
            str(self.course_updated_in_april.id),
            str(self.course_updated_in_june.id),
            str(self.course_updated_in_july.id),
        }
        admin.dump_courses(
            modeladmin=modeladmin_mock,
            request=mock.MagicMock(),
            queryset=CourseOverview.objects.filter(id__in=requested_course_keys),
        )

        # User should have been messaged
        assert modeladmin_mock.message_user.call_count == 1
        assert modeladmin_mock.message_user.call_args.args[1] == (
            "Enqueued dumps for 2 course(s). Skipped 1 unchanged course(s)."
        )

        # For enqueueing, graph should've been authenticated once, using configured settings.
        assert mock_neo4j_graph.call_count == 1
        assert mock_neo4j_graph.call_args.args == ()
        assert mock_neo4j_graph.call_args.kwargs == _coursegraph_connection

        # No errors should've been logged.
        assert mock_log_exception.call_count == 0

        # April course should have been skipped because the command was last run in May.
        # Dumps for June and July courses should have been enqueued.
        assert mock_apply_dump_task.call_count == 2
        actual_dumped_course_keys = {
            call_args.kwargs['kwargs']['course_key_string']
            for call_args in mock_apply_dump_task.call_args_list
        }
        expected_dumped_course_keys = {
            str(self.course_updated_in_june.id),
            str(self.course_updated_in_july.id),
        }
        assert actual_dumped_course_keys == expected_dumped_course_keys

    @_configure_coursegraph_connection
    @_pretend_last_course_dump_was_may_2020
    @_patch_neo4j_graph
    @_patch_apply_dump_task
    @_patch_log_exception
    def test_dump_courses_overriding_cache(self, mock_log_exception, mock_apply_dump_task, mock_neo4j_graph):
        """
        Test that dump_coursese_overriding_cach admin action dumps requested courses
        whether or not they been modified since the last dump to coursegraph.
        """
        modeladmin_mock = mock.MagicMock()

        # Request all courses except the August-updated one
        requested_course_keys = {
            str(self.course_updated_in_april.id),
            str(self.course_updated_in_june.id),
            str(self.course_updated_in_july.id),
        }
        admin.dump_courses_overriding_cache(
            modeladmin=modeladmin_mock,
            request=mock.MagicMock(),
            queryset=CourseOverview.objects.filter(id__in=requested_course_keys),
        )

        # User should have been messaged
        assert modeladmin_mock.message_user.call_count == 1
        assert modeladmin_mock.message_user.call_args.args[1] == (
            "Enqueued dumps for 3 course(s)."
        )

        # For enqueueing, graph should've been authenticated once, using configured settings.
        assert mock_neo4j_graph.call_count == 1
        assert mock_neo4j_graph.call_args.args == ()
        assert mock_neo4j_graph.call_args.kwargs == _coursegraph_connection

        # No errors should've been logged.
        assert mock_log_exception.call_count == 0

        # April, June, and July courses should have all been dumped.
        assert mock_apply_dump_task.call_count == 3
        actual_dumped_course_keys = {
            call_args.kwargs['kwargs']['course_key_string']
            for call_args in mock_apply_dump_task.call_args_list
        }
        expected_dumped_course_keys = {
            str(self.course_updated_in_april.id),
            str(self.course_updated_in_june.id),
            str(self.course_updated_in_july.id),
        }
        assert actual_dumped_course_keys == expected_dumped_course_keys

    @_configure_coursegraph_connection
    @_pretend_last_course_dump_was_may_2020
    @_make_neo4j_graph_raise
    @_patch_apply_dump_task
    @_patch_log_exception
    def test_dump_courses_error(self, mock_log_exception, mock_apply_dump_task, mock_neo4j_graph):
        """
        Test that the dump_courses admin action dumps messages the user if an error
        occurs when trying to enqueue course dumps.
        """
        modeladmin_mock = mock.MagicMock()

        # Request dump of all four courses.
        admin.dump_courses(
            modeladmin=modeladmin_mock,
            request=mock.MagicMock(),
            queryset=CourseOverview.objects.all()
        )

        # Admin user should have been messaged about failure.
        assert modeladmin_mock.message_user.call_count == 1
        assert modeladmin_mock.message_user.call_args.args[1] == (
            "Error enqueueing dumps for 4 course(s): we failed to connect or something!"
        )

        # For enqueueing, graph should've been authenticated once, using configured settings.
        assert mock_neo4j_graph.call_count == 1
        assert mock_neo4j_graph.call_args.args == ()
        assert mock_neo4j_graph.call_args.kwargs == _coursegraph_connection

        # Exception should have been logged.
        assert mock_log_exception.call_count == 1
        assert "Failed to enqueue" in mock_log_exception.call_args.args[0]

        # No courses should have been dumped.
        assert mock_apply_dump_task.call_count == 0
