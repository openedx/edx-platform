"""
This file contains a management command for exporting the modulestore to
neo4j, a graph database.
"""


import logging
from textwrap import dedent

from django.core.management.base import BaseCommand
from django.utils import six

from openedx.core.djangoapps.coursegraph.tasks import ModuleStoreSerializer

log = logging.getLogger(__name__)


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
        --secure --user user --password password --settings=production
    """
    help = dedent(__doc__).strip()

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

    def handle(self, *args, **options):
        """
        Iterates through each course, serializes them into graphs, and saves
        those graphs to neo4j.
        """

        mss = ModuleStoreSerializer.create(options['courses'], options['skip'])

        submitted_courses, skipped_courses = mss.dump_courses_to_neo4j(
            options, override_cache=options['override']
        )

        log.info(
            "%d courses submitted for export to neo4j. %d courses skipped.",
            len(submitted_courses),
            len(skipped_courses),
        )

        if not submitted_courses:
            print("No courses submitted for export to neo4j at all!")
            return

        if submitted_courses:
            print(
                "These courses were submitted for export to neo4j successfully:\n\t" +
                "\n\t".join(submitted_courses)
            )
