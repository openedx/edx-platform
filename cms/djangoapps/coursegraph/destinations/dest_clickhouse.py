import csv
import io

from django.conf import settings
from django.utils import timezone

import requests

from .dest_base import BaseCoursegraphDestination


class ClickHouseDestination(BaseCoursegraphDestination):
    connection_overrides = None
    log = None

    def __init__(self, connection_overrides, log):
        self.connection_overrides = connection_overrides
        self.log = log

    @staticmethod
    def serialize_item(item, index):
        """
        Args:
            item: an XBlock
            index: a number indicating where the item falls in the course hierarchy

        Returns:
            fields: a *limited* dictionary of an XBlock's field names and values
            block_type: the name of the XBlock's type (i.e. 'course'
            or 'problem')
        """
        from xmodule.modulestore.store_utilities import DETACHED_XBLOCK_TYPES

        course_key = item.scope_ids.usage_id.course_key
        block_type = item.scope_ids.block_type

        rtn_fields = {
            'org': course_key.org,
            'course_key': str(course_key),
            'course': course_key.course,
            'run': course_key.run,
            'location': str(item.location),
            'display_name': item.display_name_with_default.replace("'", "\'"),
            'block_type': block_type,
            'detached': 1 if block_type in DETACHED_XBLOCK_TYPES else 0,
            'edited_on': str(getattr(item, 'edited_on', '')),
            'time_last_dumped':  str(timezone.now()),
            'order': index,
        }

        return rtn_fields, block_type

    def serialize_course(self, course_id):
        """
        Serializes a course into a CSV of nodes and relationships.

        Args:
            course_id: CourseKey of the course we want to serialize

        Returns:
            nodes: a csv of nodes for the course
            relationships: a csv of relationships between nodes
        """
        # Import is placed here to avoid model import at project startup.
        from xmodule.modulestore.django import modulestore

        # create a location to node mapping we'll need later for
        # writing relationships
        location_to_node = {}
        items = modulestore().get_items(course_id)

        # create nodes
        i = 0
        for item in items:
            i += 1
            fields, block_type = self.serialize_item(item, i)
            location_to_node[self.strip_branch_and_version(item.location)] = fields

        # create relationships
        relationships = []
        for item in items:
            for index, child in enumerate(item.get_children()):
                parent_node = location_to_node.get(self.strip_branch_and_version(item.location))
                child_node = location_to_node.get(self.strip_branch_and_version(child.location))

                if parent_node is not None and child_node is not None:
                    relationship = {
                        'course_key': str(course_id),
                        'parent_location': str(parent_node["location"]),
                        'child_location': str(child_node["location"]),
                        'order': index
                    }
                    relationships.append(relationship)

        nodes = list(location_to_node.values())
        return nodes, relationships

    def dump(self, course_key):
        nodes, relationships = self.serialize_course(course_key)
        self.log.info(
            "Now dumping %s to ClickHouse: %d nodes and %d relationships",
            course_key,
            len(nodes),
            len(relationships),
        )

        course_string = str(course_key)

        try:
            # URL to a running ClickHouse server's HTTP interface. ex: https://foo.openedx.org:8443/ or
            # http://foo.openedx.org:8123/
            ch_url = settings.COURSEGRAPH_CLICKHOUSE_URL
            auth = (settings.COURSEGRAPH_CLICKHOUSE_USER, settings.COURSEGRAPH_CLICKHOUSE_PASSWORD)

            # Params that begin with "param_" will be used in the query replacement
            # all others are ClickHouse settings.
            params = {
                # Needed to actually run DELETE operations
                "allow_experimental_lightweight_delete": 1,
                # Fail early on bulk inserts
                "input_format_allow_errors_num": 1,
                "input_format_allow_errors_ratio": 0.1,
                # Used in the DELETE queries, but harmless elsewhere
                "param_course_string": course_string
            }

            del_relationships = "DELETE FROM coursegraph.coursegraph_relationships " \
                                "WHERE course_key = {course_string:String}"

            del_nodes = "DELETE FROM coursegraph.coursegraph_nodes WHERE course_key = {course_string:String}"

            for sql in (del_relationships, del_nodes):
                self.log.info(sql)
                response = requests.post(ch_url, data=sql, params=params, auth=auth)
                response.raise_for_status()
                self.log.info(response.headers)
                self.log.info(response)
                self.log.info(response.text)

            # TODO: Make these predefined queries?
            # https://clickhouse.com/docs/en/interfaces/http/#predefined_http_interface
            # "query" is a special param for the query, it's the best way to get the FORMAT CSV in there.
            params["query"] = "INSERT INTO coursegraph.coursegraph_nodes FORMAT CSV"

            output = io.StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

            for node in nodes:
                writer.writerow(node.values())

            response = requests.post(host, data=output.getvalue(), params=params, auth=auth)
            self.log.info(response.headers)
            self.log.info(response)
            self.log.info(response.text)
            response.raise_for_status()

            # Just overwriting the previous query
            params["query"] = "INSERT INTO coursegraph.coursegraph_relationships FORMAT CSV"
            output = io.StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

            for relationship in relationships:
                writer.writerow(relationship.values())

            response = requests.post(host, data=output.getvalue(), params=params, auth=auth)
            self.log.info(response.headers)
            self.log.info(response)
            self.log.info(response.text)
            response.raise_for_status()

            self.log.info("Completed dumping %s to ClickHouse", course_key)

        except Exception:  # pylint: disable=broad-except
            self.log.exception(
                "Error trying to dump course %s to ClickHouse!",
                course_string
            )
