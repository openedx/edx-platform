"""Test the clean_history management command."""

import fnmatch
from mock import Mock
from nose.plugins.attrib import attr
import os.path
import textwrap

import dateutil.parser

from django.test import TransactionTestCase
from django.db import connection

from courseware.management.commands.clean_history import StudentModuleHistoryCleaner

# In lots of places in this file, smhc == StudentModuleHistoryCleaner


def parse_date(sdate):
    """Parse a string date into a datetime."""
    parsed = dateutil.parser.parse(sdate)
    parsed = parsed.replace(tzinfo=dateutil.tz.gettz('UTC'))
    return parsed


class SmhcSayStubbed(StudentModuleHistoryCleaner):
    """StudentModuleHistoryCleaner, but with .say() stubbed for testing."""
    def __init__(self, **kwargs):
        super(SmhcSayStubbed, self).__init__(**kwargs)
        self.said_lines = []

    def say(self, msg):
        self.said_lines.append(msg)


class SmhcDbMocked(SmhcSayStubbed):
    """StudentModuleHistoryCleaner, but with db access mocked."""
    def __init__(self, **kwargs):
        super(SmhcDbMocked, self).__init__(**kwargs)
        self.get_history_for_student_modules = Mock()
        self.delete_history = Mock()

    def set_rows(self, rows):
        """Set the mocked history rows."""
        rows = [(row_id, parse_date(created)) for row_id, created in rows]
        self.get_history_for_student_modules.return_value = rows


class HistoryCleanerTest(TransactionTestCase):
    """Base class for all history cleaner tests."""

    maxDiff = None

    def setUp(self):
        super(HistoryCleanerTest, self).setUp()
        self.addCleanup(self.clean_up_state_file)

    def write_state_file(self, state):
        """Write the string `state` into the state file read by StudentModuleHistoryCleaner."""
        with open(StudentModuleHistoryCleaner.STATE_FILE, "w") as state_file:
            state_file.write(state)

    def read_state_file(self):
        """Return the string contents of the state file read by StudentModuleHistoryCleaner."""
        with open(StudentModuleHistoryCleaner.STATE_FILE) as state_file:
            return state_file.read()

    def clean_up_state_file(self):
        """Remove any state file lying around."""
        if os.path.exists(StudentModuleHistoryCleaner.STATE_FILE):
            os.remove(StudentModuleHistoryCleaner.STATE_FILE)

    def assert_said(self, smhc, *msgs):
        """Fail if the `smhc` didn't say `msgs`.

        The messages passed here are `fnmatch`-style patterns: "*" means anything.

        """
        for said, pattern in zip(smhc.said_lines, msgs):
            if not fnmatch.fnmatch(said, pattern):
                fmt = textwrap.dedent("""\
                    Messages:

                    {msgs}

                    don't match patterns:

                    {patterns}

                    Failed at {said!r} and {pattern!r}
                    """)

                msg = fmt.format(
                    msgs="\n".join(smhc.said_lines),
                    patterns="\n".join(msgs),
                    said=said,
                    pattern=pattern
                )
                self.fail(msg)

    def parse_rows(self, rows):
        """Parse convenient rows into real data."""
        rows = [
            (row_id, parse_date(created), student_module_id)
            for row_id, created, student_module_id in rows
        ]
        return rows

    def write_history(self, rows):
        """Write history rows to the db.

        Each row should be (id, created, student_module_id).

        """
        cursor = connection.cursor()
        cursor.executemany(
            """
            INSERT INTO courseware_studentmodulehistory
            (id, created, student_module_id)
            VALUES (%s, %s, %s)
            """,
            self.parse_rows(rows),
        )

    def read_history(self):
        """Read the history from the db, and return it as a list of tuples.

        Returns [(id, created, student_module_id), ...]

        """
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, created, student_module_id FROM courseware_studentmodulehistory
        """)
        return cursor.fetchall()

    def assert_history(self, rows):
        """Assert that the history rows are the same as `rows`."""
        self.assertEqual(self.parse_rows(rows), self.read_history())


@attr('shard_1')
class HistoryCleanerNoDbTest(HistoryCleanerTest):
    """Tests of StudentModuleHistoryCleaner with db access mocked."""

    def test_empty(self):
        smhc = SmhcDbMocked()
        smhc.set_rows([])

        smhc.clean_one_student_module(1)
        self.assert_said(smhc, "No history for student_module_id 1")

        # Nothing to delete, so delete_history wasn't called.
        self.assertFalse(smhc.delete_history.called)

    def test_one_row(self):
        smhc = SmhcDbMocked()
        smhc.set_rows([
            (1, "2013-07-13 12:11:10.987"),
        ])
        smhc.clean_one_student_module(1)
        self.assert_said(smhc, "Deleting 0 rows of 1 for student_module_id 1")
        # Nothing to delete, so delete_history wasn't called.
        self.assertFalse(smhc.delete_history.called)

    def test_one_row_dry_run(self):
        smhc = SmhcDbMocked(dry_run=True)
        smhc.set_rows([
            (1, "2013-07-13 12:11:10.987"),
        ])
        smhc.clean_one_student_module(1)
        self.assert_said(smhc, "Would have deleted 0 rows of 1 for student_module_id 1")
        # Nothing to delete, so delete_history wasn't called.
        self.assertFalse(smhc.delete_history.called)

    def test_two_rows_close(self):
        smhc = SmhcDbMocked()
        smhc.set_rows([
            (7, "2013-07-13 12:34:56.789"),
            (9, "2013-07-13 12:34:56.987"),
        ])
        smhc.clean_one_student_module(1)
        self.assert_said(smhc, "Deleting 1 rows of 2 for student_module_id 1")
        smhc.delete_history.assert_called_once_with([7])

    def test_two_rows_far(self):
        smhc = SmhcDbMocked()
        smhc.set_rows([
            (7, "2013-07-13 12:34:56.789"),
            (9, "2013-07-13 12:34:57.890"),
        ])
        smhc.clean_one_student_module(1)
        self.assert_said(smhc, "Deleting 0 rows of 2 for student_module_id 1")
        self.assertFalse(smhc.delete_history.called)

    def test_a_bunch_of_rows(self):
        smhc = SmhcDbMocked()
        smhc.set_rows([
            (4, "2013-07-13 16:30:00.000"),    # keep
            (8, "2013-07-13 16:30:01.100"),
            (15, "2013-07-13 16:30:01.200"),
            (16, "2013-07-13 16:30:01.300"),    # keep
            (23, "2013-07-13 16:30:02.400"),
            (42, "2013-07-13 16:30:02.500"),
            (98, "2013-07-13 16:30:02.600"),    # keep
            (99, "2013-07-13 16:30:59.000"),    # keep
        ])
        smhc.clean_one_student_module(17)
        self.assert_said(smhc, "Deleting 4 rows of 8 for student_module_id 17")
        smhc.delete_history.assert_called_once_with([42, 23, 15, 8])


@attr('shard_1')
class HistoryCleanerWitDbTest(HistoryCleanerTest):
    """Tests of StudentModuleHistoryCleaner with a real db."""

    def test_no_history(self):
        # Cleaning a student_module_id with no history leaves the db unchanged.
        smhc = SmhcSayStubbed()
        self.write_history([
            (4, "2013-07-13 16:30:00.000", 11),    # keep
            (8, "2013-07-13 16:30:01.100", 11),
            (15, "2013-07-13 16:30:01.200", 11),
            (16, "2013-07-13 16:30:01.300", 11),    # keep
            (23, "2013-07-13 16:30:02.400", 11),
            (42, "2013-07-13 16:30:02.500", 11),
            (98, "2013-07-13 16:30:02.600", 11),    # keep
            (99, "2013-07-13 16:30:59.000", 11),    # keep
        ])

        smhc.clean_one_student_module(22)
        self.assert_said(smhc, "No history for student_module_id 22")
        self.assert_history([
            (4, "2013-07-13 16:30:00.000", 11),    # keep
            (8, "2013-07-13 16:30:01.100", 11),
            (15, "2013-07-13 16:30:01.200", 11),
            (16, "2013-07-13 16:30:01.300", 11),    # keep
            (23, "2013-07-13 16:30:02.400", 11),
            (42, "2013-07-13 16:30:02.500", 11),
            (98, "2013-07-13 16:30:02.600", 11),    # keep
            (99, "2013-07-13 16:30:59.000", 11),    # keep
        ])

    def test_a_bunch_of_rows(self):
        # Cleaning a student_module_id with 8 records, 4 to delete.
        smhc = SmhcSayStubbed()
        self.write_history([
            (4, "2013-07-13 16:30:00.000", 11),    # keep
            (8, "2013-07-13 16:30:01.100", 11),
            (15, "2013-07-13 16:30:01.200", 11),
            (16, "2013-07-13 16:30:01.300", 11),    # keep
            (17, "2013-07-13 16:30:01.310", 22),    # other student_module_id!
            (23, "2013-07-13 16:30:02.400", 11),
            (42, "2013-07-13 16:30:02.500", 11),
            (98, "2013-07-13 16:30:02.600", 11),    # keep
            (99, "2013-07-13 16:30:59.000", 11),    # keep
        ])

        smhc.clean_one_student_module(11)
        self.assert_said(smhc, "Deleting 4 rows of 8 for student_module_id 11")
        self.assert_history([
            (4, "2013-07-13 16:30:00.000", 11),    # keep
            (16, "2013-07-13 16:30:01.300", 11),    # keep
            (17, "2013-07-13 16:30:01.310", 22),    # other student_module_id!
            (98, "2013-07-13 16:30:02.600", 11),    # keep
            (99, "2013-07-13 16:30:59.000", 11),    # keep
        ])

    def test_a_bunch_of_rows_dry_run(self):
        # Cleaning a student_module_id with 8 records, 4 to delete,
        # but don't really do it.
        smhc = SmhcSayStubbed(dry_run=True)
        self.write_history([
            (4, "2013-07-13 16:30:00.000", 11),    # keep
            (8, "2013-07-13 16:30:01.100", 11),
            (15, "2013-07-13 16:30:01.200", 11),
            (16, "2013-07-13 16:30:01.300", 11),    # keep
            (23, "2013-07-13 16:30:02.400", 11),
            (42, "2013-07-13 16:30:02.500", 11),
            (98, "2013-07-13 16:30:02.600", 11),    # keep
            (99, "2013-07-13 16:30:59.000", 11),    # keep
        ])

        smhc.clean_one_student_module(11)
        self.assert_said(smhc, "Would have deleted 4 rows of 8 for student_module_id 11")
        self.assert_history([
            (4, "2013-07-13 16:30:00.000", 11),    # keep
            (8, "2013-07-13 16:30:01.100", 11),
            (15, "2013-07-13 16:30:01.200", 11),
            (16, "2013-07-13 16:30:01.300", 11),    # keep
            (23, "2013-07-13 16:30:02.400", 11),
            (42, "2013-07-13 16:30:02.500", 11),
            (98, "2013-07-13 16:30:02.600", 11),    # keep
            (99, "2013-07-13 16:30:59.000", 11),    # keep
        ])

    def test_a_bunch_of_rows_in_jumbled_order(self):
        # Cleaning a student_module_id with 8 records, 4 to delete.
        smhc = SmhcSayStubbed()
        self.write_history([
            (23, "2013-07-13 16:30:01.100", 11),
            (24, "2013-07-13 16:30:01.300", 11),    # keep
            (27, "2013-07-13 16:30:02.500", 11),
            (30, "2013-07-13 16:30:01.350", 22),    # other student_module_id!
            (32, "2013-07-13 16:30:59.000", 11),    # keep
            (50, "2013-07-13 16:30:02.400", 11),
            (51, "2013-07-13 16:30:02.600", 11),    # keep
            (56, "2013-07-13 16:30:00.000", 11),    # keep
            (57, "2013-07-13 16:30:01.200", 11),
        ])

        smhc.clean_one_student_module(11)
        self.assert_said(smhc, "Deleting 4 rows of 8 for student_module_id 11")
        self.assert_history([
            (24, "2013-07-13 16:30:01.300", 11),    # keep
            (30, "2013-07-13 16:30:01.350", 22),    # other student_module_id!
            (32, "2013-07-13 16:30:59.000", 11),    # keep
            (51, "2013-07-13 16:30:02.600", 11),    # keep
            (56, "2013-07-13 16:30:00.000", 11),    # keep
        ])

    def test_a_bunch_of_rows_with_timestamp_ties(self):
        # Sometimes rows are written with identical timestamps.  The one with
        # the greater id is the winner in that case.
        smhc = SmhcSayStubbed()
        self.write_history([
            (21, "2013-07-13 16:30:01.100", 11),
            (24, "2013-07-13 16:30:01.100", 11),    # keep
            (22, "2013-07-13 16:30:01.100", 11),
            (23, "2013-07-13 16:30:01.100", 11),
            (27, "2013-07-13 16:30:02.500", 11),
            (30, "2013-07-13 16:30:01.350", 22),    # other student_module_id!
            (32, "2013-07-13 16:30:59.000", 11),    # keep
            (50, "2013-07-13 16:30:02.500", 11),    # keep
        ])

        smhc.clean_one_student_module(11)
        self.assert_said(smhc, "Deleting 4 rows of 7 for student_module_id 11")
        self.assert_history([
            (24, "2013-07-13 16:30:01.100", 11),    # keep
            (30, "2013-07-13 16:30:01.350", 22),    # other student_module_id!
            (32, "2013-07-13 16:30:59.000", 11),    # keep
            (50, "2013-07-13 16:30:02.500", 11),    # keep
        ])

    def test_get_last_student_module(self):
        # Can we find the last student_module_id properly?
        smhc = SmhcSayStubbed()
        self.write_history([
            (23, "2013-07-13 16:30:01.100", 11),
            (24, "2013-07-13 16:30:01.300", 44),
            (27, "2013-07-13 16:30:02.500", 11),
            (30, "2013-07-13 16:30:01.350", 22),
            (32, "2013-07-13 16:30:59.000", 11),
            (51, "2013-07-13 16:30:02.600", 33),
            (56, "2013-07-13 16:30:00.000", 11),
        ])
        last = smhc.get_last_student_module_id()
        self.assertEqual(last, 44)
        self.assert_said(smhc, "Last student_module_id is 44")

    def test_load_state_with_no_stored_state(self):
        smhc = SmhcSayStubbed()
        self.assertFalse(os.path.exists(smhc.STATE_FILE))
        smhc.load_state()
        self.assertEqual(smhc.next_student_module_id, 0)
        self.assert_said(smhc, "No stored state")

    def test_load_stored_state(self):
        self.write_state_file('{"next_student_module_id": 23}')
        smhc = SmhcSayStubbed()
        smhc.load_state()
        self.assertEqual(smhc.next_student_module_id, 23)
        self.assert_said(smhc, 'Loaded stored state: {"next_student_module_id": 23}')

    def test_save_state(self):
        smhc = SmhcSayStubbed()
        smhc.next_student_module_id = 47
        smhc.save_state()
        state = self.read_state_file()
        self.assertEqual(state, '{"next_student_module_id": 47}')


class SmhcForTestingMain(SmhcSayStubbed):
    """A StudentModuleHistoryCleaner with a few function stubbed for testing main."""

    def __init__(self, *args, **kwargs):
        self.exception_smids = kwargs.pop('exception_smids', ())
        super(SmhcForTestingMain, self).__init__(*args, **kwargs)

    def clean_one_student_module(self, smid):
        self.say("(not really cleaning {})".format(smid))
        if smid in self.exception_smids:
            raise Exception("Something went wrong!")


@attr('shard_1')
class HistoryCleanerMainTest(HistoryCleanerTest):
    """Tests of StudentModuleHistoryCleaner.main(), using SmhcForTestingMain."""

    def test_only_one_record(self):
        smhc = SmhcForTestingMain()
        self.write_history([
            (1, "2013-07-15 11:47:00.000", 1),
        ])
        smhc.main()
        self.assert_said(
            smhc,
            'Last student_module_id is 1',
            'No stored state',
            '(not really cleaning 0)',
            '(not really cleaning 1)',
            'Committing',
            'Saved state: {"next_student_module_id": 2}',
        )

    def test_already_processed_some(self):
        smhc = SmhcForTestingMain()
        self.write_state_file('{"next_student_module_id": 25}')
        self.write_history([
            (1, "2013-07-15 15:04:00.000", 23),
            (2, "2013-07-15 15:04:11.000", 23),
            (3, "2013-07-15 15:04:01.000", 24),
            (4, "2013-07-15 15:04:00.000", 25),
            (5, "2013-07-15 15:04:00.000", 26),
        ])
        smhc.main()
        self.assert_said(
            smhc,
            'Last student_module_id is 26',
            'Loaded stored state: {"next_student_module_id": 25}',
            '(not really cleaning 25)',
            '(not really cleaning 26)',
            'Committing',
            'Saved state: {"next_student_module_id": 27}'
        )

    def test_working_in_batches(self):
        smhc = SmhcForTestingMain()
        self.write_state_file('{"next_student_module_id": 25}')
        self.write_history([
            (3, "2013-07-15 15:04:01.000", 24),
            (4, "2013-07-15 15:04:00.000", 25),
            (5, "2013-07-15 15:04:00.000", 26),
            (6, "2013-07-15 15:04:00.000", 27),
            (7, "2013-07-15 15:04:00.000", 28),
            (8, "2013-07-15 15:04:00.000", 29),
        ])
        smhc.main(batch_size=3)
        self.assert_said(
            smhc,
            'Last student_module_id is 29',
            'Loaded stored state: {"next_student_module_id": 25}',
            '(not really cleaning 25)',
            '(not really cleaning 26)',
            '(not really cleaning 27)',
            'Committing',
            'Saved state: {"next_student_module_id": 28}',
            '(not really cleaning 28)',
            '(not really cleaning 29)',
            'Committing',
            'Saved state: {"next_student_module_id": 30}',
        )

    def test_something_failing_while_cleaning(self):
        smhc = SmhcForTestingMain(exception_smids=[26])
        self.write_state_file('{"next_student_module_id": 25}')
        self.write_history([
            (3, "2013-07-15 15:04:01.000", 24),
            (4, "2013-07-15 15:04:00.000", 25),
            (5, "2013-07-15 15:04:00.000", 26),
            (6, "2013-07-15 15:04:00.000", 27),
            (7, "2013-07-15 15:04:00.000", 28),
            (8, "2013-07-15 15:04:00.000", 29),
        ])
        smhc.main(batch_size=3)
        self.assert_said(
            smhc,
            'Last student_module_id is 29',
            'Loaded stored state: {"next_student_module_id": 25}',
            '(not really cleaning 25)',
            '(not really cleaning 26)',
            "Couldn't clean student_module_id 26:\nTraceback*Exception: Something went wrong!\n",
            '(not really cleaning 27)',
            'Committing',
            'Saved state: {"next_student_module_id": 28}',
            '(not really cleaning 28)',
            '(not really cleaning 29)',
            'Committing',
            'Saved state: {"next_student_module_id": 30}',
        )
