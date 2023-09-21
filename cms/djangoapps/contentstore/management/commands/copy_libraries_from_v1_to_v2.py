"""A Command to  Copy or uncopy V1 Content Libraries entires to be stored as v2 content libraries."""

import logging
import csv
from textwrap import dedent

from django.core.management import BaseCommand, CommandError

from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocator

from xmodule.modulestore.django import modulestore


from celery import group

from cms.djangoapps.contentstore.tasks import create_v2_library_from_v1_library, delete_v2_library_from_v1_library

from .prompt import query_yes_no

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Copy or uncopy V1 Content Libraries (default all) entires to be stored as v2 content libraries.
    First Specify the uuid for the collection to store the content libraries in.
    Specfiy --all for all libraries, library ids for specific libraries,
    and -- file followed by the path for a list of libraries from a file.

    Example usage:
        $ ./manage.py cms copy_libraries_from_v1_to_v2 'collection_uuid' --all
        $ ./manage.py cms copy_libraries_from_v1_to_v2 'collection_uuid' --all --uncopy
        $ ./manage.py cms copy_libraries_from_v1_to_v2 'collection_uuid 'library-v1:edX+DemoX+Better_Library'
        $ ./manage.py cms copy_libraries_from_v1_to_v2 'collection_uuid 'library-v1:edX+DemoX+Better_Library' --uncopy
        $ ./manage.py cms copy_libraries_from_v1_to_v2
        '11111111-2111-4111-8111-111111111111'
        './list_of--library-locators.csv --all

    Note:
       This Command Also produces an "output file" which contains the mapping of locators and the status of the copy.
    """

    help = dedent(__doc__)
    CONFIRMATION_PROMPT = "Reindexing all libraries might be a time consuming operation. Do you want to continue?"

    def add_arguments(self, parser):
        """arguements for command"""

        parser.add_argument(
            'collection_uuid',
            type=str,
            help='the uuid for the collection to create the content library in.'
        )
        parser.add_argument(
            'output_csv',
            type=str,
            nargs='?',
            default=None,
            help='a file path to write the tasks output to. Without this the result is simply logged.'
        )

        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            help='Copy all libraries'
        )
        parser.add_argument(
            '--uncopy',
            action='store_true',
            dest='uncopy',
            help='Delete libraries specified'
        )
        parser.add_argument(
            'library_ids',
            nargs='*',
            default=[],
            help='a space-seperated list of v1 library ids to copy'
        )

    def _parse_library_key(self, raw_value):
        """ Parses library key from string """
        result = CourseKey.from_string(raw_value)

        if not isinstance(result, LibraryLocator):
            raise CommandError(f"Argument {raw_value} is not a library key")
        return result

    def handle(self, *args, **options):  # lint-amnesty, pylint: disable=unused-argument
        """Parse args and generate tasks for copying content."""

        if (not options['library_ids'] and not options['all']) or (options['library_ids'] and options['all']):
            raise CommandError("copy_libraries_from_v1_to_v2 requires one or more <library_id>s or the --all flag.")

        if options['all']:
            store = modulestore()
            if query_yes_no(self.CONFIRMATION_PROMPT, default="no"):
                v1_library_keys = [
                    library.location.library_key.replace(branch=None) for library in store.get_libraries()
                ]
            else:
                return
        else:
            v1_library_keys = list(map(self._parse_library_key, options['library_ids']))

        create_library_task_group = group([
            delete_v2_library_from_v1_library.s(str(v1_library_key), options['collection_uuid'])
            if options['uncopy']
            else create_v2_library_from_v1_library.s(str(v1_library_key), options['collection_uuid'])
            for v1_library_key in v1_library_keys
        ])

        group_result = create_library_task_group.apply_async().get()
        if options['output_csv']:
            with open(options['output_csv'], 'w', encoding='utf-8', newline='') as file:
                output_writer = csv.writer(file)
                output_writer.writerow(["v1_library_id", "v2_library_id", "status", "error_msg"])
                for result in group_result:
                    output_writer.writerow(result.values())
        log.info(group_result)
