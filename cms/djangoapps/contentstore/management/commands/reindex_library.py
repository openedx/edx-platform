""" Management command to update libraries' search index """


from textwrap import dedent

from django.core.management import BaseCommand, CommandError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocator
from six.moves import map

from cms.djangoapps.contentstore.courseware_index import LibrarySearchIndexer
from xmodule.modulestore.django import modulestore

from .prompt import query_yes_no


class Command(BaseCommand):
    """
    Command to reindex content libraries (single, multiple or all available)

    Examples:

        ./manage.py reindex_library lib1 lib2 - reindexes libraries with keys lib1 and lib2
        ./manage.py reindex_library --all - reindexes all available libraries
    """
    help = dedent(__doc__)
    CONFIRMATION_PROMPT = u"Reindexing all libraries might be a time consuming operation. Do you want to continue?"

    def add_arguments(self, parser):
        parser.add_argument('library_ids', nargs='*')
        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            help='Reindex all libraries'
        )

    def _parse_library_key(self, raw_value):
        """ Parses library key from string """
        result = CourseKey.from_string(raw_value)

        if not isinstance(result, LibraryLocator):
            raise CommandError(u"Argument {0} is not a library key".format(raw_value))

        return result

    def handle(self, *args, **options):
        """
        By convention set by django developers, this method actually executes command's actions.
        So, there could be no better docstring than emphasize this once again.
        """
        if (not options['library_ids'] and not options['all']) or (options['library_ids'] and options['all']):
            raise CommandError(u"reindex_library requires one or more <library_id>s or the --all flag.")

        store = modulestore()

        if options['all']:
            if query_yes_no(self.CONFIRMATION_PROMPT, default="no"):
                library_keys = [library.location.library_key.replace(branch=None) for library in store.get_libraries()]
            else:
                return
        else:
            library_keys = list(map(self._parse_library_key, options['library_ids']))

        for library_key in library_keys:
            print(u"Indexing library {}".format(library_key))
            LibrarySearchIndexer.do_library_reindex(store, library_key)
