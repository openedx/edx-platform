"""
Django pipeline finder for handling static assets required by XBlocks.
"""
from datetime import datetime
import os
from pkg_resources import resource_exists, resource_listdir, resource_isdir, resource_filename

from xblock.core import XBlock

from django.contrib.staticfiles import utils
from django.contrib.staticfiles.finders import BaseFinder
from django.contrib.staticfiles.storage import FileSystemStorage
from django.core.files.storage import Storage


class XBlockPackageStorage(Storage):
    """
    Storage implementation for accessing XBlock package resources.
    """

    RESOURCE_PREFIX = 'xblock/resources/'

    def __init__(self, module, base_dir, *args, **kwargs):
        """
        Returns a static file storage if available in the given app.
        """
        super(XBlockPackageStorage, self).__init__(*args, **kwargs)
        self.module = module
        self.base_dir = base_dir

        # Register a prefix that collectstatic will add to each path
        self.prefix = os.path.join(self.RESOURCE_PREFIX, module)

    def path(self, name):
        """
        Returns a file system filename for the specified file name.
        """
        return resource_filename(self.module, os.path.join(self.base_dir, name))

    def exists(self, path):
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

    def accessed_time(self, name):
        """
        Returns a URL to the package resource.
        """
        return datetime.fromtimestamp(os.path.getatime(self.path(name)))

    def created_time(self, name):
        """
        Returns the created time of the package resource.
        """
        return datetime.fromtimestamp(os.path.getctime(self.path(name)))

    def modified_time(self, name):
        """
        Returns the modified time of the resource.
        """
        return datetime.fromtimestamp(os.path.getmtime(self.path(name)))

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


class XBlockPipelineFinder(BaseFinder):
    """
    A static files finder that gets static assets from xblocks.
    """
    def __init__(self, *args, **kwargs):
        super(XBlockPipelineFinder, self).__init__(*args, **kwargs)
        xblock_classes = set()
        for __, xblock_class in XBlock.load_classes():
            xblock_classes.add(xblock_class)
        self.package_storages = [
            XBlockPackageStorage(xblock_class.__module__, xblock_class.get_resources_dir())
            for xblock_class in xblock_classes
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
