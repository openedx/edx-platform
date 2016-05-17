# pylint: disable=missing-docstring

from optparse import make_option
from textwrap import dedent

from django.core.management.base import BaseCommand

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


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
        output = u'\n'.join(unicode(course_overview.id) for course_overview in CourseOverview.get_all_courses()) + '\n'

        return output
