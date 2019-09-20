"""
Management command to populate initial history for courseoverview.
"""
import logging
import time
from django.core.management.base import BaseCommand
from django.db import connection, transaction

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Populate initial history for 'courseoverview'.
    Example usage:
    $ ./manage.py lms generate_initial_history_course_overviews --batchsize 1000 --sleep_between 1 --settings=devstack
    """

    help = (
        "Populates the corresponding historical records with"
        "the current state of records which do not have a historical record yet"
    )

    DEFAULT_BATCH_SIZE = 1000
    DEFAULT_SLEEP_BETWEEN_INSERTS = 1
    DATE = '2019-06-29'
    HISTORY_USER_ID = 'NULL'
    HISTORY_CHANGE_REASON = 'initial history population'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)

        parser.add_argument(
            '--sleep_between',
            default=self.DEFAULT_SLEEP_BETWEEN_INSERTS,
            type=float,
            help='Seconds to sleep between chunked inserts.'
        )

        parser.add_argument(
            "--batchsize",
            action="store",
            default=self.DEFAULT_BATCH_SIZE,
            type=int,
            help="Maximum number of history rows to insert in each batch.",
        )

    def chunks(self, ids, chunk_size):
        for i in xrange(0, len(ids), chunk_size):
            yield ids[i:i + chunk_size]

    def handle(self, *args, **options):
        batch_size = options['batchsize']
        sleep_between = options['sleep_between']

        with connection.cursor() as cursor:
            query = u"""
                SELECT
                    t.id
                FROM course_overviews_courseoverview t
                LEFT JOIN course_overviews_historicalcourseoverview ht
                    ON t.id = ht.id
                WHERE ht.id IS NULL
                """
            cursor.execute(query)
            ids_without_history = [rows[0] for rows in cursor.fetchall()]

            if not ids_without_history:
                log.info(u"No records with missing historical records")
                return
            query = u"""
                SELECT
                    column_name
                FROM information_schema.columns
                WHERE table_name='course_overviews_courseoverview'
                ORDER BY ordinal_position
                """
            cursor.execute(query)
            columns = [column[0] for column in cursor.fetchall()]

        for chunk in self.chunks(ids_without_history, batch_size):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # xss-lint: disable=python-wrap-html
                    query = u"""
                        INSERT INTO course_overviews_historicalcourseoverview(
                            {insert_columns},history_date,history_change_reason,history_type,history_user_id
                        )
                        SELECT {select_columns},'{history_date}','{history_change_reason}', '+', {history_user_id}
                        FROM course_overviews_courseoverview t
                        LEFT JOIN course_overviews_historicalcourseoverview ht
                            ON t.id=ht.id
                        WHERE ht.id IS NULL
                            AND t.id in ({ids})
                        """.format(
                            insert_columns=','.join(columns),
                            select_columns=','.join(['t.{}'.format(c) for c in columns]),
                            history_date=self.DATE,
                            history_change_reason=self.HISTORY_CHANGE_REASON,
                            history_user_id=self.HISTORY_USER_ID,
                            ids=','.join("'{}'".format(id) for id in chunk)
                    )
                    log.info(query)
                    log.info(u"Starting insert for records with ids: %s", ','.join(chunk))
                    count = cursor.execute(query)
                    log.info(u"Inserted %s historical records", count)

            log.info(u"Sleeping %s seconds...", sleep_between)
            time.sleep(sleep_between)
