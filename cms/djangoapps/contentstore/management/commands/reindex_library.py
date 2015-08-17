""" Management command to update libraries' search index """
from django.core.management import BaseCommand, CommandError
from optparse import make_option
from textwrap import dedent

from contentstore.courseware_index import LibrarySearchIndexer

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys.edx.locator import LibraryLocator

from .prompt import query_yes_no

from xmodule.modulestore.django import modulestore


class Command(BaseCommand):
    """
    Command to reindex content libraries (single, multiple or all available)

    Examples:

        ./manage.py reindex_library lib1 lib2 - reindexes libraries with keys lib1 and lib2
        ./manage.py reindex_library --all - reindexes all available libraries
    """
    help = dedent(__doc__)

    can_import_settings = True

    args = "<library_id library_id ...>"

    option_list = BaseCommand.option_list + (
        make_option(
            '--all',
            action='store_true',
            dest='all',
            default=False,
            help='Reindex all libraries'
        ),)

    CONFIRMATION_PROMPT = u"Reindexing all libraries might be a time consuming operation. Do you want to continue?"

    def _parse_library_key(self, raw_value):
        """ Parses library key from string """
        try:
            result = CourseKey.from_string(raw_value)
        except InvalidKeyError:
            result = SlashSeparatedCourseKey.from_deprecated_string(raw_value)

        if not isinstance(result, LibraryLocator):
            raise CommandError(u"Argument {0} is not a library key".format(raw_value))

        return result

    def handle(self, *args, **options):
        """
        By convention set by django developers, this method actually executes command's actions.
        So, there could be no better docstring than emphasize this once again.
        """
        if len(args) == 0 and not options.get('all', False):
            raise CommandError(u"reindex_library requires one or more arguments: <library_id>")

        store = modulestore()

        if options.get('all', False):
            if query_yes_no(self.CONFIRMATION_PROMPT, default="no"):
                library_keys = [library.location.library_key.replace(branch=None) for library in store.get_libraries()]
            else:
                return
        else:
            library_keys = map(self._parse_library_key, args)

        for library_key in library_keys:
            LibrarySearchIndexer.do_library_reindex(store, library_key)
