"""
Script for importing a content library from a tar.gz file
"""


import base64
import os
import tarfile

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation
from django.core.management.base import BaseCommand, CommandError
from lxml import etree
from opaque_keys.edx.locator import LibraryLocator
from path import Path
from six.moves import input

from cms.djangoapps.contentstore.utils import add_instructor
from openedx.core.lib.extract_tar import safetar_extractall
from xmodule.contentstore.django import contentstore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import DuplicateCourseError
from xmodule.modulestore.xml_importer import import_library_from_xml


class Command(BaseCommand):
    """
    Import the specified content library archive.
    """
    help = 'Import the specified content library into mongo'

    def add_arguments(self, parser):
        parser.add_argument('archive_path')
        parser.add_argument('owner_username')

    def handle(self, *args, **options):
        """
        Given a content library archive path, import the corresponding course to mongo.
        """

        archive_path = options['archive_path']
        username = options['owner_username']

        data_root = Path(settings.GITHUB_REPO_ROOT)
        subdir = base64.urlsafe_b64encode(os.path.basename(archive_path))
        course_dir = data_root / subdir

        # Extract library archive
        tar_file = tarfile.open(archive_path)
        try:
            safetar_extractall(tar_file, course_dir.encode('utf-8'))
        except SuspiciousOperation as exc:
            raise CommandError(u'\n=== Course import {0}: Unsafe tar file - {1}\n'.format(archive_path, exc.args[0]))
        finally:
            tar_file.close()

        # Paths to the library.xml file
        abs_xml_path = os.path.join(course_dir, 'library')
        rel_xml_path = os.path.relpath(abs_xml_path, data_root)

        # Gather library metadata from XML file
        xml_root = etree.parse(abs_xml_path / 'library.xml').getroot()
        if xml_root.tag != 'library':
            raise CommandError(u'Failed to import {0}: Not a library archive'.format(archive_path))

        metadata = xml_root.attrib
        org = metadata['org']
        library = metadata['library']
        display_name = metadata['display_name']

        # Fetch user and library key
        user = User.objects.get(username=username)
        courselike_key, created = _get_or_create_library(org, library, display_name, user)

        # Check if data would be overwritten
        ans = ''
        while not created and ans not in ['y', 'yes', 'n', 'no']:
            inp = input(u'Library "{0}" already exists, overwrite it? [y/n] '.format(courselike_key))
            ans = inp.lower()
        if ans.startswith('n'):
            print(u'Aborting import of "{0}"'.format(courselike_key))
            return

        # At last, import the library
        try:
            import_library_from_xml(
                modulestore(), user.id,
                settings.GITHUB_REPO_ROOT, [rel_xml_path],
                load_error_modules=False,
                static_content_store=contentstore(),
                target_id=courselike_key
            )
        except Exception:
            print(u'\n=== Failed to import library-v1:{0}+{1}'.format(org, library))
            raise

        print(u'Library "{0}" imported to "{1}"'.format(archive_path, courselike_key))


def _get_or_create_library(org, number, display_name, user):
    """
    Create or retrieve given library and return its course-like key
    """

    try:
        # Create library if it does not exist
        store = modulestore()
        with store.default_store(ModuleStoreEnum.Type.split):
            library = store.create_library(
                org=org,
                library=number,
                user_id=user.id,
                fields={
                    "display_name": display_name
                },
            )
        add_instructor(library.location.library_key, user, user)
        return library.location.library_key, True
    except DuplicateCourseError:
        # Course exists, return its key
        return LibraryLocator(org=org, library=number), False
