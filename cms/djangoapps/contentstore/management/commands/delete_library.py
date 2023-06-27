"""
Management Command to delete a v1 library.
"""
import ast
import json

from cms.djangoapps.contentstore.views.library import library_blocks_view
from django.core.management.base import BaseCommand
from opaque_keys.edx.locator import BlockUsageLocator
from opaque_keys.edx.locator import LibraryLocator
from xmodule.modulestore.django import modulestore

class Command(BaseCommand):
    """
    Delete a MongoDB backed v1 library

    Example usage:
        $ ./manage.py cms delete_library '<library ID>'
    """

    help = 'Delete a MongoDB backed course'
    store = modulestore()

    def add_arguments(self, parser):
        parser.add_argument(
            'library_key',
            help='ID of the library to delete.',
        )

    def handle(self, *args, **options):

        self.store.bis_doit()
        print("Returned from bis_doit()")

        print("****** In management command to delete library  ******")
        print("For now, processing all discovered libraries equally (ignoring CLI-supplied library key)")
        # library_key = self.get_library_key(options)

        libraries = self.get_libraries()
        for lib in libraries:
            print(f'####### Processing library {lib.display_name}')
            block_usage_strings = self.display_library(lib)
            print("###### About to delete blocks in library ######")
            self.delete_library_contents(block_usage_strings)

    def get_library_key(self, **options):
        try:
            library_key = str(options['library_key'], 'utf8')
        # May already be decoded to unicode if coming in through tests, this is ok.
        except TypeError:
            library_key = str(options['library_key'])
        return library_key

    def get_libraries(self):
        print(f'"****** Looking for libraries ######')
        if not hasattr(self.store, 'get_libraries'):
            print ("###### This modulestore does not support get_libraries() ######")
        libraries = self.store.get_libraries()
        print (f'****** Found {len(libraries)} libraries ******')
        return libraries

    def get_library(self, library_key):
        library = self.store.get_library(library_key)
        if library is None:
            print("Library not found", str(library_key))
            exit(0)
        return library

    def display_library(self, lib):
        """
        Displays single library
        """
        library_key = lib.location.library_key

        # BIS DEBUG
        print ("##### Trying to get library index #######")
        index = self.store.get_course_index(library_key)
        if index is None:
            raise Exception("Index not found")
        if library_key.branch not in index['versions']:
            raise Exception("Branch not found")
        print ("######## Done getting library index ########")

        print (f"###### Trying to get library structure. branch = {library_key.branch} #######")
        version_guid = index['versions'][library_key.branch]
        entry = self.get_structure(library_key, version_guid)
        if entry is None:
            raise Exception(f'Structure: {version_guid}')
        print("###### Done getting library structure ########")

        print(f"****** Looking for block info on {str(library_key)} library")
        response_format = 'json'
        json_bytestring = library_blocks_view(lib, 'delete_library management command', response_format).content
        dict_str = json_bytestring.decode("UTF-8")
        print (f"##### dict_str = {dict_str} ##### ")
        library_dict = json.loads(dict_str)
        block_usage_strings = library_dict['blocks']
        print(f"****** Found {len(block_usage_strings)} blocks ******")

        return block_usage_strings

    def delete_library_contents(self, block_usage_strings):
        for usage_string in block_usage_strings:
            block_locator = BlockUsageLocator.from_string(usage_string)
            print(f"###### About to attempt to delete {usage_string} ######")
            self.store.delete_item(block_locator, "delete_library management command")
            print(f"###### Done deleting {usage_string} ######")
