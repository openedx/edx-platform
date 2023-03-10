"""
Todo
"""


import logging
from textwrap import dedent

from django.core.management.base import BaseCommand

from cms.djangoapps.coursegraph.tasks import ModuleStoreSerializer

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Dump recently-published course(s) over to a CourseGraph (ClickHouse) instance.
    """
    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help="the URL of the ClickHouse server",
        )
        parser.add_argument(
            '--user',
            type=str,
            help="the username of the ClickHouse user",
        )
        parser.add_argument(
            '--password',
            type=str,
            help="the password of the ClickHouse user",
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
            for key in ["url", "user", "password"]
        }
        submitted_courses, skipped_courses = mss.dump_courses_to_clickhouse(
            connection_overrides=connection_overrides,
            override_cache=options['override'],
        )

        log.info(
            "%d courses submitted for export to ClickHouse. %d courses skipped.",
            len(submitted_courses),
            len(skipped_courses),
        )

        if not submitted_courses:
            print("No courses submitted for export to ClickHouse at all!")
            return

        if submitted_courses:
            print(
                "These courses were submitted for export to ClickHouse successfully:\n\t" +
                "\n\t".join(submitted_courses)
            )
