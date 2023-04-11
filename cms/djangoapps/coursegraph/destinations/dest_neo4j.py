import logging

from django.conf import settings
from django.utils import timezone

import py2neo  # pylint: disable=unused-import
from py2neo import Graph, Node, Relationship

try:
    from py2neo.matching import NodeMatcher
except ImportError:
    from py2neo import NodeMatcher
else:
    pass

from .dest_base import BaseCoursegraphDestination


# When testing locally, neo4j's bolt logger was noisy, so we'll only have it
# emit logs if there's an error.
bolt_log = logging.getLogger('neo4j.bolt')  # pylint: disable=invalid-name
bolt_log.setLevel(logging.ERROR)

PRIMITIVE_NEO4J_TYPES = (int, bytes, str, float, bool)


class Neo4JDestination(BaseCoursegraphDestination):
    graph = None
    transaction = None
    log = None

    def __init__(self, connection_overrides, log):
        self.authenticate_and_create_graph(connection_overrides)
        self.log = log

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
        from xmodule.modulestore.store_utilities import DETACHED_XBLOCK_TYPES

        # convert all fields to a dict and filter out parent and children field
        fields = {
            field: field_value.read_from(item)
            for (field, field_value) in item.fields.items()
            if field not in ['parent', 'children']
        }

        course_key = item.scope_ids.usage_id.course_key
        block_type = item.scope_ids.block_type

        # set or reset some defaults
        fields['edited_on'] = str(getattr(item, 'edited_on', ''))
        fields['display_name'] = item.display_name_with_default
        fields['org'] = course_key.org
        fields['course'] = course_key.course
        fields['run'] = course_key.run
        fields['course_key'] = str(course_key)
        fields['location'] = str(item.location)
        fields['block_type'] = block_type
        fields['detached'] = block_type in DETACHED_XBLOCK_TYPES

        if block_type == 'course':
            # prune the checklists field
            if 'checklists' in fields:
                del fields['checklists']

            # record the time this command was run
            fields['time_last_dumped_to_neo4j'] = str(timezone.now())

        return fields, block_type

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
            coerced_value = [str(element) for element in coerced_value]

        # if it's not one of the types that neo4j accepts,
        # just convert it to text
        elif not isinstance(value, PRIMITIVE_NEO4J_TYPES):
            coerced_value = str(value)

        return coerced_value


    def add_to_transaction(self, neo4j_entities):
        """
        Add all of our entities to our transaction
        """
        for entity in neo4j_entities:
            self.transaction.create(entity)


    def get_command_last_run(self, course_key):
        """
        This information is stored on the course node of a course in neo4j
        Args:
            course_key: a CourseKey

        Returns: The datetime that the command was last run, converted into
            text, or None, if there's no record of this command last being run.
        """
        matcher = NodeMatcher(self.graph)
        course_node = matcher.match(
            "course",
            course_key=str(course_key)
        ).first()

        last_this_command_was_run = None
        if course_node:
            last_this_command_was_run = course_node['time_last_dumped_to_neo4j']

        return last_this_command_was_run


    def serialize_course(self, course_id):
        """
        Serializes a course into py2neo Nodes and Relationships
        Args:
            course_id: CourseKey of the course we want to serialize

        Returns:
            nodes: a list of py2neo Node objects
            relationships: a list of py2neo Relationships objects
        """
        # Import is placed here to avoid model import at project startup.
        from xmodule.modulestore.django import modulestore

        # create a location to node mapping we'll need later for
        # writing relationships
        location_to_node = {}
        items = modulestore().get_items(course_id)

        # create nodes
        for item in items:
            fields, block_type = self.serialize_item(item)

            for field_name, value in fields.items():
                fields[field_name] = self.coerce_types(value)

            node = Node(block_type, 'item', **fields)
            location_to_node[self.strip_branch_and_version(item.location)] = node

        # create relationships
        relationships = []
        for item in items:
            previous_child_node = None
            for index, child in enumerate(item.get_children()):
                parent_node = location_to_node.get(self.strip_branch_and_version(item.location))
                child_node = location_to_node.get(self.strip_branch_and_version(child.location))

                if parent_node is not None and child_node is not None:
                    child_node["index"] = index

                    relationship = Relationship(parent_node, "PARENT_OF", child_node)
                    relationships.append(relationship)

                    if previous_child_node:
                        ordering_relationship = Relationship(
                            previous_child_node,
                            "PRECEDES",
                            child_node,
                        )
                        relationships.append(ordering_relationship)
                    previous_child_node = child_node

        nodes = list(location_to_node.values())
        return nodes, relationships

    def authenticate_and_create_graph(self, connection_overrides=None):
        """
        This function authenticates with neo4j and creates a py2neo graph object

        Arguments:
            connection_overrides (dict): overrides to Neo4j connection
                parameters specified in `settings.COURSEGRAPH_CONNECTION`.

        Returns: a py2neo `Graph` object.
        """
        provided_overrides = {
            key: value
            for key, value in (connection_overrides or {}).items()
            # Drop overrides whose values are `None`. Note that `False` is a
            # legitimate override value that we don't want to drop here.
            if value is not None
        }
        connection_with_overrides = {**settings.COURSEGRAPH_CONNECTION, **provided_overrides}
        self.graph = Graph(**connection_with_overrides)

    def should_dump_course(self, course_key):
        """
        Only dump the course if it's been changed since the last time it's been
        dumped.
        Args:
            course_key: a CourseKey object.

        Returns:
            - whether this course should be dumped to neo4j (bool)
            - reason why course needs to be dumped (string, None if doesn't need to be dumped)
        """

        last_this_command_was_run = self.get_command_last_run(course_key)

        course_last_published_date = self.get_course_last_published(course_key)

        # if we don't have a record of the last time this command was run,
        # we should serialize the course and dump it
        if last_this_command_was_run is None:
            return (
                True,
                "no record of the last neo4j update time for the course"
            )

        # if we've serialized the course recently and we have no published
        # events, we will not dump it, and so we can skip serializing it
        # again here
        if last_this_command_was_run and course_last_published_date is None:
            return False, None

        # otherwise, serialize and dump the course if the command was run
        # before the course's last published event
        needs_update = last_this_command_was_run < course_last_published_date
        update_reason = None
        if needs_update:
            update_reason = (
                f"course has been published since last neo4j update time - "
                f"update date {last_this_command_was_run} < published date {course_last_published_date}"
            )
        return needs_update, update_reason

    def dump(self, course_key):
        nodes, relationships = self.serialize_course(course_key)
        self.log.info(
            "Now dumping %s to neo4j: %d nodes and %d relationships",
            course_key,
            len(nodes),
            len(relationships),
        )

        self.transaction = self.graph.begin()
        course_string = str(course_key)

        try:
            # first, delete existing course
            self.transaction.run(
                "MATCH (n:item) WHERE n.course_key='{}' DETACH DELETE n".format(
                    course_string
                )
            )

            # now, re-add it
            self.add_to_transaction(nodes)
            self.add_to_transaction(relationships)
            self.graph.commit(self.transaction)
            self.log.info("Completed dumping %s to neo4j", course_key)

        except Exception:  # pylint: disable=broad-except
            self.log.exception(
                "Error trying to dump course %s to neo4j, rolling back",
                course_string
            )
            self.graph.rollback(self.transaction)
