"""A command to clean the StudentModuleHistory table.

When we added XBlock storage, each field modification wrote a new history row
to the db.  Now that we have bulk saves to avoid that database hammering, we
need to clean out the unnecessary rows from the database.

This command that does that.

"""

import datetime
import json
import logging
import optparse
import time
import traceback

from django.core.management.base import NoArgsCommand
from django.db import transaction
from django.db.models import Max
from courseware.models import StudentModuleHistory


class Command(NoArgsCommand):
    """The actual clean_history command to clean history rows."""

    help = "Deletes unneeded rows from the StudentModuleHistory table."

    option_list = NoArgsCommand.option_list + (
        optparse.make_option(
            '--batch',
            type='int',
            default=100,
            help="Batch size, number of module_ids to examine in a transaction.",
        ),
        optparse.make_option(
            '--dry-run',
            action='store_true',
            default=False,
            help="Don't change the database, just show what would be done.",
        ),
        optparse.make_option(
            '--sleep',
            type='float',
            default=0,
            help="Seconds to sleep between batches.",
        ),
    )

    def handle_noargs(self, **options):
        # We don't want to see the SQL output from the db layer.
        logging.getLogger("django.db.backends").setLevel(logging.INFO)

        smhc = StudentModuleHistoryCleaner(
            dry_run=options["dry_run"],
        )
        smhc.main(batch_size=options["batch"], sleep=options["sleep"])


class StudentModuleHistoryCleaner(object):
    """Logic to clean rows from the StudentModuleHistory table."""

    DELETE_GAP_SECS = 0.5   # Rows this close can be discarded.
    STATE_FILE = "clean_history.json"
    BATCH_SIZE = 100

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.next_student_module_id = 0
        self.last_student_module_id = 0

    def main(self, batch_size=None, sleep=0):
        """Invoked from the management command to do all the work."""

        batch_size = batch_size or self.BATCH_SIZE

        transaction.enter_transaction_management()

        self.last_student_module_id = self.get_last_student_module_id()
        self.load_state()

        while self.next_student_module_id <= self.last_student_module_id:
            for smid in self.module_ids_to_check(batch_size):
                try:
                    self.clean_one_student_module(smid)
                except Exception:       # pylint: disable=broad-except
                    trace = traceback.format_exc()
                    self.say("Couldn't clean student_module_id {}:\n{}".format(smid, trace))
            if not self.dry_run:
                self.commit()
            self.save_state()
            if sleep:
                time.sleep(sleep)

    def say(self, message):
        """
        Display a message to the user.

        The message will have a trailing newline added to it.

        """
        print message

    def commit(self):
        """
        Commit the transaction.
        """
        self.say("Committing")
        transaction.commit()

    def load_state(self):
        """
        Load the latest state from disk.
        """
        try:
            state_file = open(self.STATE_FILE)
        except IOError:
            self.say("No stored state")
            self.next_student_module_id = 0
        else:
            with state_file:
                state = json.load(state_file)
            self.say(
                "Loaded stored state: {}".format(
                    json.dumps(state, sort_keys=True)
                )
            )
            self.next_student_module_id = state['next_student_module_id']

    def save_state(self):
        """
        Save the state to disk.
        """
        state = {
            'next_student_module_id': self.next_student_module_id,
        }
        with open(self.STATE_FILE, "w") as state_file:
            json.dump(state, state_file)
        self.say("Saved state: {}".format(json.dumps(state, sort_keys=True)))

    def get_last_student_module_id(self):
        """
        Return the id of the last student_module.
        """
        last = StudentModuleHistory.objects.all() \
            .aggregate(Max('student_module'))['student_module__max']
        self.say("Last student_module_id is {}".format(last))
        return last

    def module_ids_to_check(self, batch_size):
        """Produce a sequence of student module ids to check.

        `batch_size` is how many module ids to produce, max.

        The sequence starts with `next_student_module_id`, and goes up to
        and including `last_student_module_id`.

        `next_student_module_id` is updated as each id is yielded.

        """
        start = self.next_student_module_id
        for smid in range(start, start + batch_size):
            if smid > self.last_student_module_id:
                break
            yield smid
            self.next_student_module_id = smid + 1

    def get_history_for_student_modules(self, student_module_id):
        """
        Get the history rows for a student module.

        ```student_module_id```: the id of the student module we're
        interested in.

        Return a list: [(id, created), ...], all the rows of history.

        """
        history = StudentModuleHistory.objects \
            .filter(student_module=student_module_id) \
            .order_by('created', 'id')

        return [(row.id, row.created) for row in history]

    def delete_history(self, ids_to_delete):
        """
        Delete history rows.

        ```ids_to_delete```: a non-empty list (or set...) of history row ids to delete.

        """
        assert ids_to_delete
        StudentModuleHistory.objects.filter(id__in=ids_to_delete).delete()

    def clean_one_student_module(self, student_module_id):
        """Clean one StudentModule's-worth of history.

        `student_module_id`: the id of the StudentModule to process.

        """
        delete_gap = datetime.timedelta(seconds=self.DELETE_GAP_SECS)

        history = self.get_history_for_student_modules(student_module_id)
        if not history:
            self.say("No history for student_module_id {}".format(student_module_id))
            return

        ids_to_delete = []
        next_created = None
        for history_id, created in reversed(history):
            if next_created is not None:
                # Compare this timestamp with the next one.
                if (next_created - created) < delete_gap:
                    # This row is followed closely by another, we can discard
                    # this one.
                    ids_to_delete.append(history_id)

            next_created = created

        verb = "Would have deleted" if self.dry_run else "Deleting"
        self.say("{verb} {to_delete} rows of {total} for student_module_id {id}".format(
            verb=verb,
            to_delete=len(ids_to_delete),
            total=len(history),
            id=student_module_id,
        ))

        if ids_to_delete and not self.dry_run:
            self.delete_history(ids_to_delete)
