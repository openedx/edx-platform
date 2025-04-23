"""
Django pipeline finder for handling static assets required by XBlocks.
"""

import os
from datetime import datetime

from django.contrib.staticfiles import utils
from django.contrib.staticfiles.finders import BaseFinder
from django.contrib.staticfiles.storage import FileSystemStorage
from django.core.files.storage import Storage
from django.utils import timezone
from pkg_resources import resource_exists, resource_filename, resource_isdir, resource_listdir
from xblock.core import XBlock

from openedx.core.lib.xblock_utils import xblock_resource_pkg


class XBlockPackageStorage(Storage):
    """
    Storage implementation for accessing XBlock package resources.
    """

    RESOURCE_PREFIX = 'xblock/resources/'

    def __init__(self, module, base_dir, *args, **kwargs):
        """
        Returns a static file storage if available in the given app.
        """
        super().__init__(*args, **kwargs)
        self.module = module
        self.base_dir = base_dir

        # Register a prefix that collectstatic will add to each path
        self.prefix = os.path.join(self.RESOURCE_PREFIX, module)

    def path(self, name):
        """
        Returns a file system filename for the specified file name.
        """
        return resource_filename(self.module, os.path.join(self.base_dir, name))

    def exists(self, path):  # lint-amnesty, pylint: disable=arguments-differ
        """
        Returns True if the specified path exists.
        """
        if self.base_dir is None:
            return False

        return resource_exists(self.module, os.path.join(self.base_dir, path))

    def listdir(self, path):
        """
        Lists the directories beneath the specified path.
        """
        directories = []
        files = []
        for item in resource_listdir(self.module, os.path.join(self.base_dir, path)):
            __, file_extension = os.path.splitext(item)
            if file_extension not in [".py", ".pyc", ".scss"]:
                if resource_isdir(self.module, os.path.join(self.base_dir, path, item)):
                    directories.append(item)
                else:
                    files.append(item)
        return directories, files

    def open(self, name, mode='rb'):
        """
        Retrieves the specified file from storage.
        """
        path = self.path(name)
        return FileSystemStorage(path).open(path, mode)

    def size(self, name):
        """
        Returns the size of the package resource.
        """
        return os.path.getsize(self.path(name))

    def get_accessed_time(self, name):
        """
        Returns a URL to the package resource.
        """
        return datetime.fromtimestamp(os.path.getatime(self.path(name)), timezone.utc)

    def get_created_time(self, name):
        """
        Returns the created time of the package resource.
        """
        return datetime.fromtimestamp(os.path.getctime(self.path(name)), timezone.utc)

    def get_modified_time(self, name):
        """
        Returns the modified time of the resource.
        """
        return datetime.fromtimestamp(os.path.getmtime(self.path(name)), timezone.utc)

    def url(self, name):
        """
        Note: package resources do not support URLs
        """
        raise NotImplementedError("Package resources do not support URLs")

    def delete(self, name):
        """
        Note: deleting files from a package is not supported.
        """
        raise NotImplementedError("Deleting files from a package is not supported")


class XBlockPipelineFinder(BaseFinder):  # lint-amnesty, pylint: disable=abstract-method
    """
    A static files finder that gets static assets from xblocks.
    """
    def __init__(self, *args, **kwargs):
        """
        The XBlockPipelineFinder creates a separate XBlockPackageStorage for
        every installed XBlock package when its initialized. After that
        initialization happens, we just proxy all list()/find() requests by
        iterating through the XBlockPackageStorage objects.
        """
        super().__init__(*args, **kwargs)

        # xblock_resource_info holds (package_name, resources_dir) tuples. While
        # it never happens in practice, the XBlock API does allow different
        # XBlocks installed with the same setup.py to refer to their shared
        # static assets using different prefixes.
        xblock_resource_info = {
            (xblock_resource_pkg(xblock_class), xblock_class.get_resources_dir())
            for __, xblock_class in XBlock.load_classes()
        }
        self.package_storages = [
            XBlockPackageStorage(pkg_name, resources_dir)
            for pkg_name, resources_dir in xblock_resource_info
        ]

    def list(self, ignore_patterns):
        """
        List all static files in all xblock packages.
        """
        for storage in self.package_storages:
            if storage.exists(''):  # check if storage location exists
                for path in utils.get_files(storage, ignore_patterns):
                    yield path, storage

    def find(self, path, all=False):  # pylint: disable=redefined-builtin
        """
        Looks for files in the xblock package directories.
        """
        matches = []
        for storage in self.package_storages:
            if storage.exists(path):
                match = storage.path(path)
                if not all:
                    return match
                matches.append(match)
        return matches
