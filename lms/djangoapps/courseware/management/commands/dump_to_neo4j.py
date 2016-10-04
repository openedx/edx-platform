"""
This file contains a management command for exporting the modulestore to
neo4j, a graph database.
"""
from __future__ import unicode_literals

import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import six
from py2neo import Graph, Node, Relationship, authenticate
from py2neo.compat import integer, string, unicode as neo4j_unicode
from request_cache.middleware import RequestCache
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)

# When testing locally, neo4j's bolt logger was noisy, so we'll only have it
# emit logs if there's an error.
bolt_log = logging.getLogger('neo4j.bolt')  # pylint: disable=invalid-name
bolt_log.setLevel(logging.ERROR)

ITERABLE_NEO4J_TYPES = (tuple, list, set, frozenset)
PRIMITIVE_NEO4J_TYPES = (integer, string, neo4j_unicode, float, bool)


class ModuleStoreSerializer(object):
    """
    Class with functionality to serialize a modulestore into subgraphs,
    one graph per course.
    """
    def __init__(self):
        self.all_courses = modulestore().get_course_summaries()

    @staticmethod
    def serialize_item(item):
        """
        Args:
            item: an XBlock

        Returns:
            fields: a dictionary of an XBlock's field names and values
            label: the name of the XBlock's type (i.e. 'course'
            or 'problem')
        """
        # convert all fields to a dict and filter out parent and children field
        fields = dict(
            (field, field_value.read_from(item))
            for (field, field_value) in six.iteritems(item.fields)
            if field not in ['parent', 'children']
        )

        course_key = item.scope_ids.usage_id.course_key

        # set or reset some defaults
        fields['edited_on'] = six.text_type(getattr(item, 'edited_on', ''))
        fields['display_name'] = item.display_name_with_default
        fields['org'] = course_key.org
        fields['course'] = course_key.course
        fields['run'] = course_key.run
        fields['course_key'] = six.text_type(course_key)

        label = item.scope_ids.block_type

        # prune some fields
        if label == 'course':
            if 'checklists' in fields:
                del fields['checklists']

        return fields, label

    def serialize_course(self, course_id):
        """
        Args:
            course_id: CourseKey of the course we want to serialize

        Returns:
            nodes: a list of py2neo Node objects
            relationships: a list of py2neo Relationships objects

        Serializes a course into Nodes and Relationships
        """
        # create a location to node mapping we'll need later for
        # writing relationships
        location_to_node = {}
        items = modulestore().get_items(course_id)

        # create nodes
        nodes = []
        for item in items:
            fields, label = self.serialize_item(item)

            for field_name, value in six.iteritems(fields):
                fields[field_name] = self.coerce_types(value)

            node = Node(label, 'item', **fields)
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
        value is iterable, the value with each element being converted to text
        """

        coerced_value = value
        if isinstance(value, ITERABLE_NEO4J_TYPES):
            coerced_value = []
            for element in value:
                coerced_value.append(six.text_type(element))
            # convert coerced_value back to its original type
            coerced_value = type(value)(coerced_value)

        # if it's not one of the types that neo4j accepts,
        # just convert it to text
        elif not isinstance(value, PRIMITIVE_NEO4J_TYPES):
            coerced_value = six.text_type(value)

        return coerced_value


class Command(BaseCommand):
    """
    Command to dump modulestore data to neo4j

    Takes the following named arguments:
      host: the host of the neo4j server
      port: the port on the server that accepts https requests
      user: the username for the neo4j user
      password: the user's password

    Example usage:
      python manage.py lms dump_to_neo4j --host localhost --port 7473 \
        --user user --password password --settings=aws
    """
    def add_arguments(self, parser):
        parser.add_argument('--host', type=unicode)
        parser.add_argument('--port', type=int)
        parser.add_argument('--user', type=unicode)
        parser.add_argument('--password', type=unicode)

    @staticmethod
    def add_to_transaction(neo4j_entities, transaction):
        """
        Args:
            neo4j_entities: a list of Nodes or Relationships
            transaction: a neo4j transaction
        """
        for entity in neo4j_entities:
            transaction.create(entity)

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        """
        Iterates through each course, serializes them into graphs, and saves
        those graphs to neo4j.
        """
        host = options['host']
        port = options['port']
        neo4j_user = options['user']
        neo4j_password = options['password']

        authenticate(
            "{host}:{port}".format(host=host, port=port),
            neo4j_user,
            neo4j_password,
        )

        graph = Graph(
            bolt=True,
            password=neo4j_password,
            user=neo4j_user,
            https_port=port,
            host=host,
            secure=True
        )

        mss = ModuleStoreSerializer()

        total_number_of_courses = len(mss.all_courses)

        for index, course in enumerate(mss.all_courses):
            # first, clear the request cache to prevent memory leaks
            RequestCache.clear_request_cache()

            log.info(
                "Now exporting %s to neo4j: course %d of %d total courses",
                course.id,
                index + 1,
                total_number_of_courses
            )
            nodes, relationships = mss.serialize_course(course.id)
            log.info(
                "%d nodes and %d relationships in %s",
                len(nodes),
                len(relationships),
                course.id
            )

            transaction = graph.begin()
            try:
                # first, delete existing course
                transaction.run(
                    "MATCH (n:item) WHERE n.course_key='{}' DETACH DELETE n".format(
                        six.text_type(course.id)
                    )
                )

                # now, re-add it
                self.add_to_transaction(nodes, transaction)
                self.add_to_transaction(relationships, transaction)
                transaction.commit()

            except Exception:  # pylint: disable=broad-except
                log.exception(
                    "Error trying to dump course %s to neo4j, rolling back",
                    six.text_type(course.id)
                )
                transaction.rollback()
