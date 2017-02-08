# pragma: no cover
"""
Fix StudentModule entries that have Course IDs with trailing newlines.

Due to a bug, many rows in courseware_studentmodule were written with a
course_id that had a trailing newline. This command tries to fix that, and to
merge that data with data that might have been written to the correct course_id.
"""
from collections import namedtuple
from optparse import make_option
from textwrap import dedent
import json
import logging

from django.db import DatabaseError
from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from courseware.models import StudentModule
from util.query import use_read_replica_if_available

log = logging.getLogger("fix_student_module_newlines")

FixResult = namedtuple('FixResult', 'record_trimmed data_copied record_archived capa_merge error')


class Command(BaseCommand):
    """Fix StudentModule entries that have Course IDs with trailing newlines."""
    args = "<start_date> <end_date>"
    help = dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
        make_option('--dry_run',
                    action='store_true',
                    default=False,
                    help="Run read queries and say what we're going to do, but don't actually do it."),
    )

    def handle(self, *args, **options):
        """Fix newline courses in CSM!"""
        if len(args) != 2:
            raise CommandError('Must specify start and end dates: e.g. "2016-08-23 16:43:00" "2016-08-24 22:00:00"')

        start, end = args
        dry_run = options['dry_run']

        log.info(
            "Starting fix_student_module_newlines in %s mode!",
            "dry_run" if dry_run else "real"
        )

        rows_to_fix = use_read_replica_if_available(
            # pylint: disable=no-member
            StudentModule.objects.raw(
                "select * from courseware_studentmodule where modified between %s and %s and course_id like %s",
                (start, end, '%\n')
            )
        )

        results = [self.fix_row(row, dry_run=dry_run) for row in rows_to_fix]
        log.info(
            "Finished fix_student_module_newlines in %s mode!",
            "dry_run" if dry_run else "real"
        )
        log.info("Stats: %s rows detected", len(results))
        if results:
            # Add up all the columns
            aggregated_result = FixResult(*[sum(col) for col in zip(*results)])
            log.info("Results: %s", aggregated_result)

    def fix_row(self, read_only_newline_course_row, dry_run=False):
        """
        Fix a StudentModule with a trailing newline in the course_id.

        Returns a count of (row modified, )

        At the end of this method call, the record should no longer have a
        trailing newline for the course_id. There are three possible outcomes:

        1. There was never a conflicting entry:
            -> We just update this row.
        2. Conflict and the other row (with correct course_id) wins:
            -> We archive this row.
        2. Conflict and this row wins:
            -> We copy the data to the conflicting row (the one that has a
               correct course_id), and archive this row.

        Even though all the StudentModule entries coming in here have trailing
        newlines in the course_id, the deserialization logic will obscure that
        (it gets parsed out when read from the database). We will also
        automatically strip the newlines when writing back to the database, so
        we have to be very careful about violating unique constraints by doing
        unintended updates. That's why we only do an update to
        newline_course_row if no correct_course_row exists.
        """
        # pylint: disable=too-many-statements
        # We got the StudentModule from the read replica, so we have to fetch it
        # again from our writeable database before making changes
        log.info(
            "Fixing row %s, course %s, student %s, block %s",
            read_only_newline_course_row.id,
            read_only_newline_course_row.course_id,
            read_only_newline_course_row.student_id,
            read_only_newline_course_row.module_state_key,
        )
        try:
            newline_course_row = StudentModule.objects.get(id=read_only_newline_course_row.id)
        except StudentModule.DoesNotExist:
            # We're not going to be able to make any corrective writes, so just fail fast
            log.exception("Could not find editable CSM row %s", read_only_newline_course_row.id)
            return FixResult(record_trimmed=0, data_copied=0, record_archived=0, capa_merge=0, error=1)

        # Find the StudentModule entry with the correct course_id.
        try:
            correct_course_row = StudentModule.objects.get(
                student_id=newline_course_row.student_id,
                course_id=newline_course_row.course_id,
                module_state_key=newline_course_row.module_state_key,
            )
            assert correct_course_row.pk != newline_course_row.pk
        except StudentModule.DoesNotExist:
            correct_course_row = None

        # If only an entry with the newline course exists, just change the course_id and save.
        if correct_course_row is None:
            log.info(
                "No conflict: Removing trailing newline from course_id in CSM row %s - (%s) %s",
                newline_course_row.id,
                newline_course_row.module_type,
                newline_course_row.module_state_key,
            )
            if dry_run:
                return FixResult(record_trimmed=1, data_copied=0, record_archived=0, capa_merge=0, error=0)

            try:
                with transaction.atomic():
                    newline_course_row.save()
                return FixResult(record_trimmed=1, data_copied=0, record_archived=0, capa_merge=0, error=0)
            except DatabaseError:
                log.exception(
                    "Could not remove newline and update CSM row %s", newline_course_row.id
                )
                return FixResult(record_trimmed=0, data_copied=0, record_archived=0, capa_merge=0, error=1)

        # If we're here, then both versions of the row exist. We're going to
        # pick a winner. This is handled differently for capa (where we have to
        # merge entries) and everything else.
        #
        # Handle CAPA record merging!
        if newline_course_row.module_type == 'problem':
            return self.handle_capa_merge(correct_course_row, newline_course_row, dry_run)

        row_to_keep = self.row_to_keep(correct_course_row, newline_course_row)

        # To minimize the chances of conflicts and preserve history, if we
        # decided to keep the data from the newline_course_row, we copy that
        # data into correct_course_row, and then archive the newline_course_row
        # as a cleanup step.
        if row_to_keep.id == newline_course_row.id:
            log.info(
                "Conflict: Choosing data from newline course, copying data from CSM %s to %s - (%s) %s",
                newline_course_row.id,
                correct_course_row.id,
                newline_course_row.module_type,
                newline_course_row.module_state_key
            )
            correct_course_row.state = newline_course_row.state
            correct_course_row.grade = newline_course_row.grade
            correct_course_row.max_grade = newline_course_row.max_grade

            if dry_run:
                return FixResult(record_trimmed=0, data_copied=1, record_archived=1, capa_merge=0, error=0)

            try:
                with transaction.atomic():
                    correct_course_row.save()
                    self.cleanup_row(newline_course_row)
                return FixResult(record_trimmed=0, data_copied=1, record_archived=1, capa_merge=0, error=0)
            except DatabaseError:
                log.exception(
                    "Failed while trying save CSM row %s and archiving row %s",
                    correct_course_row.id,
                    newline_course_row.id
                )
                return FixResult(record_trimmed=0, data_copied=0, record_archived=0, capa_merge=0, error=1)

        # If we've reached this point, we just want to keep correct_course_row
        # and delete the newline_course_row entry.
        log.info(
            "Conflict: Choosing data from record with correct course_id (%s) "
            "and archiving row with newline in course_id (%s) - (%s) %s",
            correct_course_row.id,
            newline_course_row.id,
            newline_course_row.module_type,
            newline_course_row.module_state_key
        )

        if dry_run:
            return FixResult(record_trimmed=0, data_copied=0, record_archived=1, capa_merge=0, error=0)

        try:
            with transaction.atomic():
                self.cleanup_row(newline_course_row)
            return FixResult(record_trimmed=0, data_copied=0, record_archived=1, capa_merge=0, error=0)
        except DatabaseError:
            log.exception("Could not archive CSM row %s", newline_course_row.id)
            return FixResult(record_trimmed=0, data_copied=0, record_archived=0, capa_merge=0, error=1)

    def cleanup_row(self, model):
        """Rename the row for archiving purposes"""
        new_run = model.course_id.run.strip() + "_FIX_FOR_ECOM-5345"
        model.course_id = model.course_id.replace(run=new_run)
        model.save()

    def handle_capa_merge(self, correct_course_row, newline_course_row, dry_run):
        """
        Merge capa state and grades, if possible.
        """
        log.info(
            "-> Merging capa grade and state information for CSM rows %s (newline) and %s (correct course_id)",
            newline_course_row.id,
            correct_course_row.id
        )
        state, grade, max_grade = self.capa_state_and_grade(
            correct_course_row, newline_course_row
        )
        # The derived grade should match at least one of the two records
        nl_grade_tuple = (newline_course_row.grade, newline_course_row.max_grade)
        cc_grade_tuple = (correct_course_row.grade, correct_course_row.max_grade)
        safe_to_change_grade = (grade, max_grade) in [nl_grade_tuple, cc_grade_tuple]
        if not safe_to_change_grade:
            log.error(
                "-> Derived grade %s does not match grades from either %s %s or "
                "%s %s -- Archiving newline entry %s and leaving %s alone",
                (grade, max_grade),
                newline_course_row.id,
                nl_grade_tuple,
                correct_course_row.id,
                cc_grade_tuple,
                newline_course_row.id,
                correct_course_row.id,
            )

        safe_to_change_result = FixResult(record_trimmed=0, data_copied=0, record_archived=1, capa_merge=1, error=0)
        not_safe_to_change_result = FixResult(record_trimmed=0, data_copied=0, record_archived=1, capa_merge=0, error=1)

        if dry_run:
            return safe_to_change_result if safe_to_change_grade else not_safe_to_change_result

        try:
            with transaction.atomic():
                if safe_to_change_grade:
                    correct_course_row.state = state
                    correct_course_row.grade = grade
                    correct_course_row.max_grade = max_grade
                    correct_course_row.save()
                self.cleanup_row(newline_course_row)
            return safe_to_change_result if safe_to_change_grade else not_safe_to_change_result
        except DatabaseError:
            log.exception("Failed while trying to merge capa CSM row %s (newline) and %s (correct course_id)")
            return FixResult(record_trimmed=0, data_copied=0, record_archived=0, capa_merge=0, error=1)

    def capa_state_and_grade(self, correct_course_row, newline_course_row):
        """
        Return a tuple that is (state, grade, max_grade) to preserve.

        THIS SHOULD ONLY BE CALLED FOR CAPA PROBLEMS.

        Updates to scores could have gotten crossed with updates to state, so
        that the states and scores do not match up to each other (e.g. you might
        have correct_course_row with the proper state, but the score
        corresponding to that state might live in newline_course_row). So we're
        going to re-derive the scores from the state for capa problems.
        """
        ccr_grade, ccr_max_grade = self.grade_for_state(correct_course_row.state)
        if (ccr_grade, ccr_max_grade) != (correct_course_row.grade, correct_course_row.max_grade):
            log.info(
                "-> Correct course row %s has grade %s but should have grade %s",
                correct_course_row.id,
                (correct_course_row.grade, correct_course_row.max_grade),
                (ccr_grade, ccr_max_grade)
            )

        ncr_grade, ncr_max_grade = self.grade_for_state(newline_course_row.state)
        if (ncr_grade, ncr_max_grade) != (newline_course_row.grade, newline_course_row.max_grade):
            log.info(
                "-> Newline course row %s has grade %s but should have grade %s",
                newline_course_row.id,
                (newline_course_row.grade, newline_course_row.max_grade),
                (ncr_grade, ncr_max_grade)
            )

        if ncr_grade > ccr_grade:
            log.info(
                "-> Newline course row %s has higher derived grade for state.",
                newline_course_row.id
            )
            return newline_course_row.state, ncr_grade, ncr_max_grade

        log.info(
            "-> Correct course row %s has higher or equal derived grade for state.",
            correct_course_row.id
        )
        return correct_course_row.state, ccr_grade, ccr_max_grade

    def grade_for_state(self, state):
        """Given unparsed state, return the (grade, max_grade) we should have."""
        parsed_state = json.loads(state)
        correct_map = parsed_state.get("correct_map")
        if not correct_map:
            input_state = parsed_state.get('input_state')
            if input_state is not None:
                return 0.0, float(len(input_state))
            return None, None

        def item_score(item):
            """Return score for an individual correct_map entry."""
            # Partial credit overrides all, even if correctness is 'incorrect'.
            # We're inconsistent on whether we say the correctness is
            # 'incorrect' or 'partially-correct' in this situation.
            partial_points = item.get('npoints')
            if partial_points is not None:
                return partial_points

            # Otherwise, we're either right or wrong.
            correctness = item.get('correctness')
            if correctness in ['correct', 'partially-correct']:
                return 1.0

            return 0.0

        grade = sum(item_score(item) for item in correct_map.values())
        max_grade = float(len(correct_map))

        return grade, max_grade

    def row_to_keep(self, correct_course_row, newline_course_row):
        """Determine which row's data we want to keep."""
        # Rule 1: Take the higher grade.
        if newline_course_row.grade > correct_course_row.grade:
            log.info(
                "-> Newline course record grade %s is higher than correct course record grade %s",
                newline_course_row.grade,
                correct_course_row.grade
            )
            return newline_course_row
        elif correct_course_row.grade > newline_course_row.grade:
            log.info(
                "-> Correct course record grade %s is higher than newline course record grade %s",
                correct_course_row.grade,
                newline_course_row.grade
            )
            return correct_course_row

        # Rule 2: Take the newline course record if they've interacted with it
        #         more recently.
        if newline_course_row.modified > correct_course_row.modified:
            log.info(
                "-> Newline course record modified %s is later than correct course record modified %s",
                newline_course_row.modified,
                correct_course_row.modified
            )
            return newline_course_row

        # In all other cases, take the correct_course_row
        return correct_course_row
