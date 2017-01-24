"""
This file contains a management command for exporting the modulestore to
neo4j, a graph database.
"""
from __future__ import unicode_literals, print_function

import logging

from django.core.management.base import BaseCommand
from django.utils import six, timezone
from opaque_keys.edx.keys import CourseKey
from py2neo import Graph, Node, Relationship, authenticate, NodeSelector
from py2neo.compat import integer, string, unicode as neo4j_unicode
from request_cache.middleware import RequestCache
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.store_utilities import DETACHED_XBLOCK_TYPES

from openedx.core.djangoapps.content.course_structures.models import CourseStructure

log = logging.getLogger(__name__)

# When testing locally, neo4j's bolt logger was noisy, so we'll only have it
# emit logs if there's an error.
bolt_log = logging.getLogger('neo4j.bolt')  # pylint: disable=invalid-name
bolt_log.setLevel(logging.ERROR)

PRIMITIVE_NEO4J_TYPES = (integer, string, neo4j_unicode, float, bool)


class ModuleStoreSerializer(object):
    """
    Class with functionality to serialize a modulestore into subgraphs,
    one graph per course.
    """

    def __init__(self, courses=None, skip=None):
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
        if courses:
            course_keys = [CourseKey.from_string(course.strip()) for course in courses]
        else:
            course_keys = [
                course.id for course in modulestore().get_course_summaries()
            ]
        if skip is not None:
            skip_keys = [CourseKey.from_string(course.strip()) for course in skip]
            course_keys = [course_key for course_key in course_keys if course_key not in skip_keys]
        self.course_keys = course_keys

    @staticmethod
    def serialize_item(item):
        """
        Args:
            item: an XBlock

        Returns:
            fields: a dictionary of an XBlock's field names and values
            block_type: the name of the XBlock's type (i.e. 'course'
            or 'problem')
        """
        # convert all fields to a dict and filter out parent and children field
        fields = dict(
            (field, field_value.read_from(item))
            for (field, field_value) in six.iteritems(item.fields)
            if field not in ['parent', 'children']
        )

        course_key = item.scope_ids.usage_id.course_key
        block_type = item.scope_ids.block_type

        # set or reset some defaults
        fields['edited_on'] = six.text_type(getattr(item, 'edited_on', ''))
        fields['display_name'] = item.display_name_with_default
        fields['org'] = course_key.org
        fields['course'] = course_key.course
        fields['run'] = course_key.run
        fields['course_key'] = six.text_type(course_key)
        fields['location'] = six.text_type(item.location)
        fields['block_type'] = block_type
        fields['detached'] = block_type in DETACHED_XBLOCK_TYPES

        if block_type == 'course':
            # prune the checklists field
            if 'checklists' in fields:
                del fields['checklists']

            # record the time this command was run
            fields['time_last_dumped_to_neo4j'] = six.text_type(timezone.now())

        return fields, block_type

    def serialize_course(self, course_id):
        """
        Serializes a course into py2neo Nodes and Relationships
        Args:
            course_id: CourseKey of the course we want to serialize

        Returns:
            nodes: a list of py2neo Node objects
            relationships: a list of py2neo Relationships objects
        """
        # create a location to node mapping we'll need later for
        # writing relationships
        location_to_node = {}
        items = modulestore().get_items(course_id)

        # create nodes
        nodes = []
        for item in items:
            fields, block_type = self.serialize_item(item)

            for field_name, value in six.iteritems(fields):
                fields[field_name] = self.coerce_types(value)

            node = Node(block_type, 'item', **fields)
            nodes.append(node)
            location_to_node[item.location] = node

        # create relationships
        relationships = []
        for item in items:
            for child_loc in item.get_children():
                parent_node = location_to_node.get(item.location)
                child_node = location_to_node.get(child_loc.location)
                if parent_node is not None and child_node is not None:
                    relationship = Relationship(parent_node, "PARENT_OF", child_node)
                    relationships.append(relationship)

        return nodes, relationships

    @staticmethod
    def coerce_types(value):
        """
        Args:
            value: the value of an xblock's field

        Returns: either the value, a text version of the value, or, if the
            value is a list, a list where each element is converted to text.
        """
        coerced_value = value
        if isinstance(value, list):
            coerced_value = [six.text_type(element) for element in coerced_value]

        # if it's not one of the types that neo4j accepts,
        # just convert it to text
        elif not isinstance(value, PRIMITIVE_NEO4J_TYPES):
            coerced_value = six.text_type(value)

        return coerced_value

    @staticmethod
    def add_to_transaction(neo4j_entities, transaction):
        """
        Args:
            neo4j_entities: a list of Nodes or Relationships
            transaction: a neo4j transaction
        """
        for entity in neo4j_entities:
            transaction.create(entity)

    @staticmethod
    def get_command_last_run(course_key, graph):
        """
        This information is stored on the course node of a course in neo4j
        Args:
            course_key: a CourseKey
            graph: a py2neo Graph

        Returns: The datetime that the command was last run, converted into
            text, or None, if there's no record of this command last being run.

        """
        selector = NodeSelector(graph)
        course_node = selector.select(
            "course",
            course_key=six.text_type(course_key)
        ).first()

        last_this_command_was_run = None
        if course_node:
            last_this_command_was_run = course_node['time_last_dumped_to_neo4j']

        return last_this_command_was_run

    @staticmethod
    def get_course_last_published(course_key):
        """
        We use the CourseStructure table to get when this course was last
        published.
        Args:
            course_key: a CourseKey

        Returns: The datetime the course was last published at, converted into
            text, or None, if there's no record of the last time this course
            was published.
        """
        try:
            structure = CourseStructure.objects.get(course_id=course_key)
            course_last_published_date = six.text_type(structure.modified)
        except CourseStructure.DoesNotExist:
            course_last_published_date = None

        return course_last_published_date

    def should_dump_course(self, course_key, graph):
        """
        Only dump the course if it's been changed since the last time it's been
        dumped.
        Args:
            course_key: a CourseKey object.
            graph: a py2neo Graph object.

        Returns: bool of whether this course should be dumped to neo4j.
        """

        last_this_command_was_run = self.get_command_last_run(course_key, graph)

        course_last_published_date = self.get_course_last_published(course_key)

        # if we don't have a record of the last time this command was run,
        # we should serialize the course and dump it
        if last_this_command_was_run is None:
            return True

        # if we've serialized the course recently and we have no published
        # events, we will not dump it, and so we can skip serializing it
        # again here
        if last_this_command_was_run and course_last_published_date is None:
            return False

        # otherwise, serialize and dump the course if the command was run
        # before the course's last published event
        return last_this_command_was_run < course_last_published_date

    def dump_courses_to_neo4j(self, graph, override_cache=False):
        """
        Method that iterates through a list of courses in a modulestore,
        serializes them, then writes them to neo4j
        Args:
            graph: py2neo graph object
            override_cache: serialize the courses even if they'be been recently
                serialized

        Returns: two lists--one of the courses that were successfully written
            to neo4j and one of courses that were not.
        """

        total_number_of_courses = len(self.course_keys)

        successful_courses = []
        unsuccessful_courses = []

        for index, course_key in enumerate(self.course_keys):
            # first, clear the request cache to prevent memory leaks
            RequestCache.clear_request_cache()

            log.info(
                "Now exporting %s to neo4j: course %d of %d total courses",
                course_key,
                index + 1,
                total_number_of_courses,
            )

            if not (override_cache or self.should_dump_course(course_key, graph)):
                log.info("skipping dumping %s, since it hasn't changed", course_key)
                continue

            nodes, relationships = self.serialize_course(course_key)
            log.info(
                "%d nodes and %d relationships in %s",
                len(nodes),
                len(relationships),
                course_key,
            )

            transaction = graph.begin()
            course_string = six.text_type(course_key)
            try:
                # first, delete existing course
                transaction.run(
                    "MATCH (n:item) WHERE n.course_key='{}' DETACH DELETE n".format(
                        course_string
                    )
                )

                # now, re-add it
                self.add_to_transaction(nodes, transaction)
                self.add_to_transaction(relationships, transaction)
                transaction.commit()

            except Exception:  # pylint: disable=broad-except
                log.exception(
                    "Error trying to dump course %s to neo4j, rolling back",
                    course_string
                )
                transaction.rollback()
                unsuccessful_courses.append(course_string)

            else:
                successful_courses.append(course_string)

        return successful_courses, unsuccessful_courses


class Command(BaseCommand):
    """
    Command to dump modulestore data to neo4j

    Takes the following named arguments:
      host: the host of the neo4j server
      https_port: the port on the neo4j server that accepts https requests
      http_port: the port on the neo4j server that accepts http requests
      secure: if set, connects to server over https, otherwise uses http
      user: the username for the neo4j user
      password: the user's password
      courses: list of course key strings to serialize. If not specified, all
        courses in the modulestore are serialized.
      override: if true, dump all--or all specified--courses, regardless of when
        they were last dumped. If false, or not set, only dump those courses that
        were updated since the last time the command was run.

    Example usage:
      python manage.py lms dump_to_neo4j --host localhost --https_port 7473 \
        --secure --user user --password password --settings=aws
    """
    def add_arguments(self, parser):
        parser.add_argument('--host', type=six.text_type)
        parser.add_argument('--https_port', type=int, default=7473)
        parser.add_argument('--http_port', type=int, default=7474)
        parser.add_argument('--secure', action='store_true')
        parser.add_argument('--user', type=six.text_type)
        parser.add_argument('--password', type=six.text_type)
        parser.add_argument('--courses', type=six.text_type, nargs='*')
        parser.add_argument('--skip', type=six.text_type, nargs='*')
        parser.add_argument(
            '--override',
            action='store_true',
            help='dump all--or all specified--courses, ignoring cache',
        )

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        """
        Iterates through each course, serializes them into graphs, and saves
        those graphs to neo4j.
        """
        host = options['host']
        https_port = options['https_port']
        http_port = options['http_port']
        secure = options['secure']
        neo4j_user = options['user']
        neo4j_password = options['password']

        authenticate(
            "{host}:{port}".format(host=host, port=https_port if secure else http_port),
            neo4j_user,
            neo4j_password,
        )

        graph = Graph(
            bolt=True,
            password=neo4j_password,
            user=neo4j_user,
            https_port=https_port,
            http_port=http_port,
            host=host,
            secure=secure,
        )

        mss = ModuleStoreSerializer(options['courses'], options['skip'])

        successful_courses, unsuccessful_courses = mss.dump_courses_to_neo4j(
            graph, override_cache=options['override']
        )

        if not successful_courses and not unsuccessful_courses:
            print("No courses exported to neo4j at all!")
            return

        if successful_courses:
            print(
                "These courses exported to neo4j successfully:\n\t" +
                "\n\t".join(successful_courses)
            )
        else:
            print("No courses exported to neo4j successfully.")

        if unsuccessful_courses:
            print(
                "These courses did not export to neo4j successfully:\n\t" +
                "\n\t".join(unsuccessful_courses)
            )
        else:
            print("All courses exported to neo4j successfully.")
