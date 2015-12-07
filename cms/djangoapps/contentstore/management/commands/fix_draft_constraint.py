"""Script for deleting orphans"""
from django.core.management.base import BaseCommand, CommandError
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore


class Command(BaseCommand):
    """Checks and ensures a course obeys the draft constraint"""
    help = "Copies missing draft ids from the published to draft branch of a course"

    def handle(self, *args, **options):
        "Execute the command"
        if len(args) not in {1, 2}:
            raise CommandError("`fix_draft_constraints` requires one or more arguments: <course_id> |commit|")

        the_args = args
        course_key = CourseKey.from_string(the_args[0])

        commit = False
        if len(args) == 2:
            commit = args[1] == 'commit'

        # for now only support on split mongo
        # pylint: disable=protected-access
        owning_store = modulestore()._get_modulestore_for_courselike(course_key)
        if hasattr(owning_store, 'fix_draft_constraint'):
            missing_blocks, commit = owning_store.fix_draft_constraint(course_key, ModuleStoreEnum.UserID.mgmt_command, commit)
        else:
            raise CommandError("The owning modulestore does not support this command.")

        if commit and missing_blocks:
            print(
                u"These blocks were added to the draft branch of {course}:\n\t{blocks}".format(
                    course=unicode(course_key),
                    blocks="\n\t".join(missing_blocks)
                )
            )
        elif missing_blocks:
            print(
                u"These blocks are missing from the draft branch of {course}:\n\t{blocks}".format(
                    course=unicode(course_key),
                    blocks="\n\t".join(missing_blocks)
                )
            )
        else:
            print(u"This course ({course}) satisfies the draft constraint.".format(
                course=unicode(course_key)
            ))
