"""
Command to import modulestore content into Content Libraries.
"""

import argparse
import collections
import logging

import requests

from django.conf import settings
from django.core.management import BaseCommand
from django.core.management import CommandError

from edx_rest_api_client.client import OAuthAPIClient
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import LibraryLocatorV2
from opaque_keys.edx.locator import LibraryUsageLocatorV2
from openedx.core.djangoapps.content_libraries import api as contentlib_api
from openedx.core.djangoapps.olx_rest_api.block_serializer import XBlockSerializer
from xmodule.modulestore.django import modulestore


log = logging.getLogger(__name__)


class BaseEdxImportClient:
    """
    Base class for all import clients used by this command.

    Import clients are wrappers tailored to implement the steps used in the
    import command and can leverage different backends. It is not aimed towards
    being a generic API client for Open edX.
    """

    EXPORTABLE_BLOCK_TYPES = {"drag-and-drop-v2",
                              "problem",
                              "html",
                              "video"}

    def get_block_data(self, block_key):
        """
        Get the block's OLX and static files, if any.
        """
        raise NotImplementedError()

    def get_export_keys(self, course_key):
        """
        Get all exportable block keys of a given course.
        """
        raise NotImplementedError()

    def get_block_static_data(self, asset_file):
        """
        Get the contents of an asset_file specified in the block_olx
        """
        raise NotImplementedError()


class EdxModulestoreClient(BaseEdxImportClient):
    """
    An import client based on the local instance of modulestore.
    """

    def __init__(self, modulestore_instance=None):
        """
        Initialize the client with a modulestore instance.
        """
        self.modulestore = modulestore_instance or modulestore()

    def get_block_data(self, block_key):
        """
        Get block OLX by serializing it from modulestore directly.
        """
        block = self.modulestore.get_item(block_key)
        data = XBlockSerializer(block)
        return {'olx': data.olx_str,
                'static_file': {s.name: s for s in data.static_files}}

    def get_export_keys(self, course_key):
        """
        Retrieve the course from modulestore and traverse its content tree.
        """
        course = self.modulestore.get_course(course_key)
        export_keys = set()
        blocks_q = collections.deque(course.get_children())
        while blocks_q:
            block = blocks_q.popleft()
            usage_id = block.scope_ids.usage_id
            if usage_id in export_keys:
                continue
            if usage_id.block_type in self.EXPORTABLE_BLOCK_TYPES:
                export_keys.add(usage_id)
            if block.has_children:
                blocks_q.extend(block.get_children())
        return list(export_keys)

    def get_block_static_data(self, asset_file):
        """
        Get static content from its URL if available, otherwise from its data.
        """
        if asset_file.data:
            return asset_file.data
        resp = requests.get(f"http://{settings.CMS_BASE}" + asset_file.url)
        resp.raise_for_status()
        return resp.content


class EdxApiClient(BaseEdxImportClient):
    """
    An import client based on a remote Open Edx API interface.
    """

    URL_COURSES = "/api/courses/v1/courses/{course_key}"

    URL_MODULESTORE_BLOCK_OLX = "/api/olx-export/v1/xblock/{block_key}/"

    def __init__(self, lms_url, studio_url, oauth_key, oauth_secret):
        """
        Initialize the API client with URLs and OAuth keys.
        """
        self.lms_url = lms_url
        self.studio_url = studio_url
        self.oauth_client = OAuthAPIClient(
            self.lms_url,
            oauth_key,
            oauth_secret,
        )

    def get_block_data(self, block_key):
        """
        See parent's docstring.
        """
        olx_path = self.URL_MODULESTORE_BLOCK_OLX.format(block_key=block_key)
        resp = self._get(self.studio_url + olx_path)
        return resp['blocks'][str(block_key)]

    def get_export_keys(self, course_key):
        """
        See parent's docstring.
        """
        course_blocks_url = self._get_course(course_key)['blocks_url']
        course_blocks = self._get(
            course_blocks_url,
            params={'all_blocks': True, 'depth': 'all'})['blocks']
        export_keys = []
        for block_info in course_blocks.values():
            if block_info['type'] in self.EXPORTABLE_BLOCK_TYPES:
                export_keys.append(UsageKey.from_string(block_info['id']))
        return export_keys

    def get_block_static_data(self, asset_file):
        """
        See parent's docstring.
        """
        if (asset_file["url"].startswith(self.studio_url)
                and 'export-file' in asset_file['url']):
            # We must call download this file with authentication. But
            # we only want to pass the auth headers if this is the same
            # studio instance, or else we could leak credentials to a
            # third party.
            path = asset_file['url'][len(self.studio_url):]
            resp = self._get(path)
        else:
            resp = requests.get(asset_file['url'])
        resp.raise_for_status()
        return resp.content

    def _get(self, *args, **kwds):
        """
        Perform a get request to the client.
        """
        return self._json_call('get', *args, **kwds)

    def _get_course(self, course_key):
        """
        Request details for a course.
        """
        course_url = self.lms_url + self.URL_COURSES.format(course_key=course_key)
        return self._get(course_url)

    def _json_call(self, method, *args, **kwds):
        """
        Wrapper around request calls that ensures valid json responses.
        """
        response = getattr(self.oauth_client, method)(*args, **kwds)
        response.raise_for_status()
        return response.json()


class Command(BaseCommand):
    """
    Import modulestore content, references by a course, into a Content Libraries
    library.
    """

    def add_arguments(self, parser):
        """
        Add arguments to the argument parser.
        """
        parser.add_argument(
            'library-key',
            type=LibraryLocatorV2.from_string,
            help=('Usage key of the Content Library to import content into.'),
        )
        parser.add_argument(
            'course-key',
            type=CourseKey.from_string,
            help=('The Course Key string, used to identify the course to import '
                  'content from.'),
        )
        subparser = parser.add_subparsers(
            title='Courseware location and methods',
            dest='method',
            description=('Select the method and location to locate the course and '
                         'its contents.')
        )
        api_parser = subparser.add_parser(
            'api',

            help=('Query and retrieve course blocks from a remote instance using '
                  'Open edX course and OLX export APIs.  You need to enable API access '
                  'on the instance.')
        )
        api_parser.add_argument(
            '--lms-url',
            default=settings.LMS_ROOT_URL,
            help=("The LMS URL, used to retrieve course content (default: "
                  "'%(default)s')."),
        )
        api_parser.add_argument(
            '--studio-url',
            default=f"https://{settings.CMS_BASE}",
            help=("The Studio URL, used to retrieve block OLX content (default: "
                  "'%(default)s')"),
        )
        oauth_group = api_parser.add_mutually_exclusive_group(required=False)
        oauth_group.add_argument(
            '--oauth-creds-file',
            type=argparse.FileType('r'),
            help=('The edX OAuth credentials in a filename.  The first line is '
                  'the OAuth key, second line is the OAuth secret.  This is '
                  'preferred compared to passing the credentials in the command '
                  'line.'),
        )
        oauth_group.add_argument(
            '--oauth-creds',
            nargs=2,
            help=('The edX OAuth credentials in the command line.  The first '
                  'argument is the OAuth secret, the second argument is the '
                  'OAuth key. Notice that command line arguments are insecure, '
                  'see `--oauth-creds-file`.'),
        )
        subparser.add_parser(
            'modulestore',
            help=("Use a local modulestore intsance to retrieve blocks database on "
                  "the instance where the command is being run.  You don't need "
                  "to enable API access.")
        )

    def write_error(self, *args, **kwds):
        """
        Write error messagses to stdout.
        """
        return self.stdout.write(self.style.ERROR(*args, **kwds))

    def write_success(self, *args, **kwds):
        """
        Write success messages to stdout.
        """
        return self.stdout.write(self.style.SUCCESS(*args, **kwds))

    def handle(self, *args, **options):
        """
        Collect all blocks from a course that are "importable" and write them to the
        a blockstore library.
        """

        # Search for the library.

        try:
            library = contentlib_api.get_library(options['library-key'])
        except contentlib_api.ContentLibraryNotFound as exc:
            raise CommandError("The library specified does not exist: "
                               f"{options['library-key']}") from exc

        # Validate the method and its arguments, instantiate the openedx client.

        if options['method'] == 'api':
            if options['oauth_creds_file']:
                with options['oauth_creds_file'] as creds_f:
                    oauth_key, oauth_secret = [v.strip() for v in creds_f.readlines()]
            elif options['oauth_creds']:
                oauth_key, oauth_secret = options['oauth_creds']
            else:
                raise CommandError("Method 'remote' requires one of the "
                                   "--oauth-* options, and none was specified.")
            edx_client = EdxApiClient(
                options['lms_url'],
                options['studio_url'],
                oauth_key,
                oauth_secret)
        elif options['method'] == 'modulestore':
            edx_client = EdxModulestoreClient()
        else:
            assert False, f"Method not supported: {options['method']}"

        # Query the course and rerieve all course blocks.

        export_keys = edx_client.get_export_keys(options['course-key'])
        if not export_keys:
            raise CommandError("The courseware course specified does not have "
                               "any exportable content.  No action take.")

        # Import each block, skipping the ones that fail.

        failed_blocks = []
        for index, block_key in enumerate(export_keys):
            try:
                self.stdout.write(f"{index + 1}/{len(export_keys)}: {block_key}: ", ending='')
                self.import_block(edx_client, library, block_key)
            except Exception as exc:  # pylint: disable=broad-except
                self.write_error('❌')
                self.stderr.write(f"Failed to import modulestore block: {exc}")
                log.exception("Error importing modulestore block: %s", block_key)
                failed_blocks.append(block_key)
                continue
            else:
                self.write_success('✓')
        if failed_blocks:
            self.write_error(f"❌ {len(failed_blocks)} out of {len(export_keys)} failed:")
            for key in failed_blocks:
                self.write_error(str(key))

    def import_block(self, edx_client, library, modulestore_key):
        """
        Import a single modulestore block.
        """

        # Get or create the block in the library.

        block_data = edx_client.get_block_data(modulestore_key)

        try:
            library_block = contentlib_api.create_library_block(
                library.key,
                modulestore_key.block_type,
                modulestore_key.block_id)
            blockstore_key = library_block.usage_key
        except contentlib_api.LibraryBlockAlreadyExists:
            blockstore_key = LibraryUsageLocatorV2(
                lib_key=library.key,
                block_type=modulestore_key.block_type,
                usage_id=modulestore_key.block_id,
            )
            contentlib_api.get_library_block(blockstore_key)

        # Handle static files.

        for filename, static_file in block_data.get('static_files', {}).items():
            files = [
                f.path for f in
                contentlib_api.get_library_block_static_asset_files(blockstore_key)
            ]
            if filename in files:
                # Files already added, move on.
                continue
            file_content = edx_client.get_block_static_data(static_file)
            contentlib_api.add_library_block_static_asset_file(
                blockstore_key, filename, file_content)

        # Import OLX and publish.

        contentlib_api.set_library_block_olx(blockstore_key, block_data['olx'])
        contentlib_api.publish_changes(blockstore_key.lib_key)
