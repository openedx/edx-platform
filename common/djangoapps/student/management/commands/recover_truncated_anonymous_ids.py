"""
Generate sql commands to fix truncated anonymous student ids in the ORA database
"""
import sys

from django.core.management.base import NoArgsCommand

from student.models import AnonymousUserId, anonymous_id_for_user


class Command(NoArgsCommand):
    help = __doc__

    def handle_noargs(self, **options):
        """
        Reads a list of ids (newline separated) from stdin, and
        dumps sql queries to run on the ORA database to fix those ids
        from their truncated form to the full 32 character change.

        The following query will generate the list of ids needed to be fixed
        from the ORA database:

        SELECT student_id FROM peer_grading_calibrationhistory WHERE LENGTH(student_id) = 16
        UNION SELECT student_id FROM controller_submission WHERE LENGTH(student_id) = 16
        UNION SELECT student_id FROM metrics_timing WHERE LENGTH(student_id) = 16
        UNION SELECT student_id FROM metrics_studentcourseprofile WHERE LENGTH(student_id) = 16
        UNION SELECT student_id FROM metrics_studentprofile WHERE LENGTH(student_id) = 16;
        """

        ids = [line.strip() for line in sys.stdin]

        old_ids = AnonymousUserId.objects.raw(
            """
                SELECT *
                FROM student_anonymoususerid_temp_archive
                WHERE anonymous_user_id IN ({})
            """.format(','.join(['%s']*len(ids))),
            ids
        )

        for old_id in old_ids:
            new_id = anonymous_id_for_user(old_id.user, old_id.course_id)

            for table in ('peer_grading_calibrationhistory', 'controller_submission', 'metrics_timing'):
                self.stdout.write(
                    "UPDATE {} "
                    "SET student_id = '{}' "
                    "WHERE student_id = '{}';\n".format(
                        table,
                        new_id,
                        old_id.anonymous_user_id,
                    )
                )

            self.stdout.write(
                "DELETE FROM metrics_studentcourseprofile "
                "WHERE student_id = '{}' "
                "AND problems_attempted = 0;\n".format(old_id.anonymous_user_id)
            )

            self.stdout.write(
                "DELETE FROM metrics_studentprofile "
                "WHERE student_id = '{}' "
                "AND messages_sent = 0 "
                "AND messages_received = 0 "
                "AND average_message_feedback_length = 0 "
                "AND student_is_staff_banned = 0 "
                "AND student_cannot_submit_more_for_peer_grading = 0;\n".format(old_id.anonymous_user_id)
            )
