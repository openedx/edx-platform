###
### Script for editing the course's tabs
###

#
# Run it this way:
#   ./manage.py cms --settings dev edit_course_tabs --course Stanford/CS99/2013_spring
#
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from .prompt import query_yes_no

from courseware.courses import get_course_by_id

from contentstore.views import tabs


def print_course(course):
    "Prints out the course id and a numbered list of tabs."
    print course.id
    print 'num type name'
    for index, item in enumerate(course.tabs):
        print index + 1, '"' + item.get('type') + '"', '"' + item.get('name', '') + '"'


# course.tabs looks like this
# [{u'type': u'courseware'}, {u'type': u'course_info', u'name': u'Course Info'}, {u'type': u'textbooks'},
# {u'type': u'discussion', u'name': u'Discussion'}, {u'type': u'wiki', u'name': u'Wiki'},
# {u'type': u'progress', u'name': u'Progress'}]


class Command(BaseCommand):
    help = """See and edit a course's tabs list. Only supports insertion
and deletion. Move and rename etc. can be done with a delete
followed by an insert. The tabs are numbered starting with 1.
Tabs 1 and 2 cannot be changed, and tabs of type static_tab cannot
be edited (use Studio for those).

As a first step, run the command with a courseid like this:
  --course Stanford/CS99/2013_spring
This will print the existing tabs types and names. Then run the
command again, adding --insert or --delete to edit the list.
"""
    # Making these option objects separately, so can refer to their .help below
    course_option = make_option('--course',
                                action='store',
                                dest='course',
                                default=False,
                                help='--course <id> required, e.g. Stanford/CS99/2013_spring')
    delete_option = make_option('--delete',
                                action='store_true',
                                dest='delete',
                                default=False,
                                help='--delete <tab-number>')
    insert_option = make_option('--insert',
                                action='store_true',
                                dest='insert',
                                default=False,
                                help='--insert <tab-number> <type> <name>, e.g. 2 "course_info" "Course Info"')

    option_list = BaseCommand.option_list + (course_option, delete_option, insert_option)

    def handle(self, *args, **options):
        if not options['course']:
            raise CommandError(Command.course_option.help)

        course = get_course_by_id(options['course'])

        print 'Warning: this command directly edits the list of course tabs in mongo.'
        print 'Tabs before any changes:'
        print_course(course)

        try:
            if options['delete']:
                if len(args) != 1:
                    raise CommandError(Command.delete_option.help)
                num = int(args[0])
                if query_yes_no('Deleting tab {0} Confirm?'.format(num), default='no'):
                    tabs.primitive_delete(course, num - 1)  # -1 for 0-based indexing
            elif options['insert']:
                if len(args) != 3:
                    raise CommandError(Command.insert_option.help)
                num = int(args[0])
                tab_type = args[1]
                name = args[2]
                if query_yes_no('Inserting tab {0} "{1}" "{2}" Confirm?'.format(num, tab_type, name), default='no'):
                    tabs.primitive_insert(course, num - 1, tab_type, name)  # -1 as above
        except ValueError as e:
            # Cute: translate to CommandError so the CLI error prints nicely.
            raise CommandError(e)
