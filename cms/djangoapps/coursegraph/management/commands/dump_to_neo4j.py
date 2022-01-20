"""
This file contains a management command for exporting the modulestore to
neo4j, a graph database.
"""


import logging
from textwrap import dedent

from django.core.management.base import BaseCommand

from cms.djangoapps.coursegraph.tasks import ModuleStoreSerializer

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command to dump modulestore data to neo4j

    Takes the following named arguments:
      host: the host of the neo4j server
      port: the port on the neo4j server that accepts Bolt requests
      secure: if set, connects to server over Bolt/TLS, otherwise uses Bolt
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
        parser.add_argument('--host', type=str)
        parser.add_argument('--port', type=int, default=7687)
        parser.add_argument('--secure', action='store_true')
        parser.add_argument('--user', type=str)
        parser.add_argument('--password', type=str)
        parser.add_argument('--courses', type=str, nargs='*')
        parser.add_argument('--skip', type=str, nargs='*')
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
