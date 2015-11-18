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
        store = modulestore()
        name = options['modulestore']
        if name != 'default':
            # since a store type is given, get that specific store
            if hasattr(store, '_get_modulestore_by_type'):
                store = store._get_modulestore_by_type(name)
            if store.get_modulestore_type() != name:
                raise CommandError("Modulestore {} not found".format(name))

        if store is None:
            raise CommandError("Unknown modulestore {}".format(name))
        output = u'\n'.join(unicode(course.id) for course in store.get_courses()) + '\n'

        return output
