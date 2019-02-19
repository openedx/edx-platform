from __future__ import print_function

import logging
import textwrap

from django.core.management.base import BaseCommand
from django.db import connection


LOG = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', default=False, action='store_true')
        parser.add_argument('from_date')
        parser.add_argument('course_id')

    def handle(self, *args, **options):
        query = textwrap.dedent(
            """
            UPDATE
                schedules_schedule s
            JOIN student_courseenrollment e ON e.id = s.enrollment_id
            JOIN course_overviews_courseoverview c ON c.id = e.course_id
            SET s.start = c.start
            WHERE
                s.start < c.start
                AND s.start > %s
                AND c.start < CURRENT_DATE()
                AND c.id = %s;
            """
        )
        parameters = [options['from_date'], options['course_id']]
        if options['dry_run']:
            print(query)
            print(parameters)
        else:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                print('Rows updated: {}'.format(cursor.rowcount))
