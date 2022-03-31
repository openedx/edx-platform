"""
This file contains a management command for exporting the modulestore to
Neo4j, a graph database.

Example usages:

    # Dump all courses published since last dump.
    # Use connection parameters from `settings.COURSEGRAPH_SETTINGS`.
    python manage.py cms dump_to_neo4j

    # Dump all courses published since last dump.
    # Use custom connection parameters.
    python manage.py cms dump_to_neo4j --host localhost --port 7473 \
      --secure --user user --password password

    # Specify certain courses instead of dumping all of them.
    # Use connection parameters from `settings.COURSEGRAPH_SETTINGS`.
    python manage.py cms dump_to_neo4j --courses 'course-v1:A+B+1' 'course-v1:A+B+2'
"""


import logging
from textwrap import dedent

from django.core.management.base import BaseCommand

from cms.djangoapps.coursegraph.tasks import ModuleStoreSerializer

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Dump recently-published course(s) over to a CourseGraph (Neo4j) instance.
    """
    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            type=str,
            help="the hostname of the Neo4j server",
        )
        parser.add_argument(
            '--port',
            type=int,
            help="the port on the Neo4j server that accepts Bolt requests",
        )
        parser.add_argument(
            '--secure',
            action='store_true',
            help="connect to server over Bolt/TLS instead of plain unencrypted Bolt",
        )
        parser.add_argument(
            '--user',
            type=str,
            help="the username of the Neo4j user",
        )
        parser.add_argument(
            '--password',
            type=str,
            help="the password of the Neo4j user",
        )
        parser.add_argument(
            '--courses',
            metavar='KEY',
            type=str,
            nargs='*',
            help="keys of courses to serialize; if omitted all courses in system are serialized",
        )
        parser.add_argument(
            '--skip',
            metavar='KEY',
            type=str,
            nargs='*',
            help="keys of courses to NOT to serialize",
        )
        parser.add_argument(
            '--override',
            action='store_true',
            help="dump all courses regardless of when they were last published",
        )

    def handle(self, *args, **options):
        """
        Iterates through each course, serializes them into graphs, and saves
        those graphs to neo4j.
        """

        mss = ModuleStoreSerializer.create(options['courses'], options['skip'])
        connection_overrides = {
            key: options[key]
            for key in ["host", "port", "secure", "user", "password"]
        }
        submitted_courses, skipped_courses = mss.dump_courses_to_neo4j(
            connection_overrides=connection_overrides,
            override_cache=options['override'],
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
