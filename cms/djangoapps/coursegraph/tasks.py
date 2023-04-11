"""
This file contains a management command for exporting the modulestore to
neo4j, a graph database.
"""

import logging

from celery import shared_task
from edx_django_utils.cache import RequestCache
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.keys import CourseKey

from destinations.dest_clickhouse import ClickHouseDestination
from destinations.dest_neo4j import Neo4JDestination

log = logging.getLogger(__name__)
celery_log = logging.getLogger('edx.celery.task')


@shared_task
@set_code_owner_attribute
def dump_course_to_clickhouse(course_key_string, connection_overrides=None):
    """
    Serializes a course and writes it to neo4j.

    Arguments:
        course_key_string: course key for the course to be exported
        connection_overrides (dict):  overrides to ClickHouse connection
            parameters specified in `settings.COURSEGRAPH_CONNECTION`.
    """
    course_key = CourseKey.from_string(course_key_string)
    destination = ClickHouseDestination(connection_overrides=connection_overrides, log=celery_log)
    destination.dump(course_key)


@shared_task
@set_code_owner_attribute
def dump_course_to_neo4j(course_key_string, connection_overrides=None):
    """
    Serializes a course and writes it to neo4j.

    Arguments:
        course_key_string: course key for the course to be exported
        connection_overrides (dict):  overrides to Neo4j connection
            parameters specified in `settings.COURSEGRAPH_CONNECTION`.
    """
    course_key = CourseKey.from_string(course_key_string)
    destination = Neo4JDestination(connection_overrides=connection_overrides, log=celery_log)
    destination.dump(course_key)


class ModuleStoreSerializer:
    """
    Class with functionality to serialize a modulestore into subgraphs,
    one graph per course.
    """

    def __init__(self, course_keys):
        self.course_keys = course_keys

    @classmethod
    def create(cls, courses=None, skip=None):
        """
        Sets the object's course_keys attribute from the `courses` parameter.
        If that parameter isn't furnished, loads all course_keys from the
        modulestore.
        Filters out course_keys in the `skip` parameter, if provided.
        Args:
            courses: A list of string serializations of course keys.
                For example, ["course-v1:org+course+run"].
            skip: Also a list of string serializations of course keys.
        """
        # Import is placed here to avoid model import at project startup.
        from xmodule.modulestore.django import modulestore
        if courses:
            course_keys = [CourseKey.from_string(course.strip()) for course in courses]
        else:
            course_keys = [
                course.id for course in modulestore().get_course_summaries()
            ]
        if skip is not None:
            skip_keys = [CourseKey.from_string(course.strip()) for course in skip]
            course_keys = [course_key for course_key in course_keys if course_key not in skip_keys]
        return cls(course_keys)

    def dump_courses_to_clickhouse(self, connection_overrides=None, override_cache=False):
        """
        Iterates through a list of courses in a modulestore, serializes them to csv,
        then submits tasks to post them to ClickHouse.

        Arguments:
            connection_overrides (dict): overrides to ClickHouse connection
                parameters specified in `settings.COURSEGRAPH_CONNECTION`.
            override_cache: serialize the courses even if they've been recently
                serialized

        Returns: two lists--one of the courses that were successfully written
            to ClickHouse and one of courses that were not.
        """
        total_number_of_courses = len(self.course_keys)

        submitted_courses = []
        skipped_courses = []

        for index, course_key in enumerate(self.course_keys):
            # first, clear the request cache to prevent memory leaks
            RequestCache.clear_all_namespaces()

            (needs_dump, reason) = (True, "")  # TODO: should_dump_course_clickhouse(course_key)

            if not override_cache and not needs_dump:
                log.info("skipping submitting %s, since it hasn't changed", course_key)
                skipped_courses.append(str(course_key))
                continue

            if override_cache:
                reason = "override_cache is True"

            log.info(
                "Now submitting %s for export to ClickHouse, because %s: course %d of %d total courses",
                course_key,
                reason,
                index + 1,
                total_number_of_courses,
            )

            dump_course_to_clickhouse.apply_async(
                kwargs=dict(
                    course_key_string=str(course_key),
                    connection_overrides=connection_overrides,
                )
            )
            submitted_courses.append(str(course_key))

        return submitted_courses, skipped_courses

    def dump_courses_to_neo4j(self, connection_overrides=None, override_cache=False):
        """
        Method that iterates through a list of courses in a modulestore,
        serializes them, then submits tasks to write them to neo4j.
        Arguments:
            connection_overrides (dict): overrides to Neo4j connection
                parameters specified in `settings.COURSEGRAPH_CONNECTION`.
            override_cache: serialize the courses even if they've been recently
                serialized

        Returns: two lists--one of the courses that were successfully written
            to neo4j and one of courses that were not.
        """

        total_number_of_courses = len(self.course_keys)

        submitted_courses = []
        skipped_courses = []

        graph = Neo4JDestination.authenticate_and_create_graph(connection_overrides=connection_overrides)

        for index, course_key in enumerate(self.course_keys):
            # first, clear the request cache to prevent memory leaks
            RequestCache.clear_all_namespaces()

            (needs_dump, reason) = Neo4JDestination.should_dump_course(course_key, graph)
            if not (override_cache or needs_dump):
                log.info("skipping submitting %s, since it hasn't changed", course_key)
                skipped_courses.append(str(course_key))
                continue

            if override_cache:
                reason = "override_cache is True"

            log.info(
                "Now submitting %s for export to neo4j, because %s: course %d of %d total courses",
                course_key,
                reason,
                index + 1,
                total_number_of_courses,
            )

            dump_course_to_neo4j.apply_async(
                kwargs=dict(
                    course_key_string=str(course_key),
                    connection_overrides=connection_overrides,
                )
            )
            submitted_courses.append(str(course_key))

        return submitted_courses, skipped_courses
