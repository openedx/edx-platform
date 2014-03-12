# pylint: disable=missing-docstring

from optparse import make_option
from textwrap import dedent

from django.core.management.base import BaseCommand, CommandError

from xmodule.modulestore.django import modulestore


class Command(BaseCommand):
    """
    Simple command to dump the course_ids available to the lms.

    Output is UTF-8 encoded by default.

    """
    help = dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
        make_option('--modulestore',
                    action='store',
                    default='default',
                    help='Name of the modulestore to use'),
    )

    def handle(self, *args, **options):
        results = []

        try:
            name = options['modulestore']
            store = modulestore(name)
        except KeyError:
            raise CommandError("Unknown modulestore {}".format(name))

        for course in store.get_courses():
            course_id = course.location.course_id
            results.append(course_id)

        output = '\n'.join(results) + '\n'

        return output.encode('utf-8')
