import os
from urllib.parse import urljoin

from bson import ObjectId
from bson.errors import InvalidId
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.utils.encoding import filepath_to_uri

from gridfs import GridFS, NoFile


def _get_subcollections(collection):
    """
    Returns all sub-collections of `collection`.
    """
    # XXX: Use the MongoDB API for this once it exists.
    for name in collection.database.collection_names():
        cleaned = name[:name.rfind('.')]
        if cleaned != collection.name and cleaned.startswith(collection.name):
            yield cleaned


@deconstructible
class GridFSStorage(Storage):
    """
    GridFS Storage backend for Django.
    Based on https://github.com/django-nonrel/mongodb-engine/blob/master/django_mongodb_engine/storage.py

    This backend aims to add a GridFS storage to upload files to
    using Django's file fields.

    For performance, the file hierarchy is represented as a tree of
    MongoDB sub-collections.

    (One could use a flat list, but to list a directory '/this/path/'
    we would have to execute a search over the whole collection and
    then filter the results to exclude those not starting by
    '/this/path' using that model.)

    :param location:
       (optional) Name of the top-level node that holds the files. This
       value of `location` is prepended to all file paths, so it works
       like the `location` setting for Django's built-in
       :class:`~django.core.files.storage.FileSystemStorage`.
    :param collection:
        Name of the collection the file tree shall be stored in.
        Defaults to 'storage'.
    :param database:
        Alias of the Django database to use. Defaults to 'default' (the
        default Django database).
    :param base_url:
        URL that serves the files in GridFS (for instance, through
        nginx-gridfs).
        Defaults to None (file not accessible through a URL).
    """

    def __init__(self, location='', collection='storage', database='default',
                 base_url=None):
        self.location = location.strip(os.sep)
        self.collection = collection
        self.database = database
        self.base_url = base_url

        if not self.collection:
            raise ImproperlyConfigured("'collection' may not be empty.")

        if self.base_url and not self.base_url.endswith('/'):
            raise ImproperlyConfigured("If set, 'base_url' must end with a "
                                       "slash.")

    def _open(self, path, mode='rb'):
        """
        Returns a :class:`~gridfs.GridOut` file opened in `mode`, or
        raises :exc:`~gridfs.errors.NoFile` if the requested file
        doesn't exist and mode is not 'w'.
        """
        gridfs, filename = self._get_gridfs(path)
        try:
            return gridfs.get_last_version(filename)
        except NoFile:
            if 'w' in mode:
                return gridfs.new_file(filename=filename)
            else:
                raise

    def _save(self, path, content):
        """
        Saves `content` into the file at `path`.
        """
        gridfs, filename = self._get_gridfs(path)
        gridfs.put(content, filename=filename, contentType=content.content_type)
        return path

    def delete(self, path):
        """
        Deletes the file at `path` if it exists.
        """
        gridfs, filename = self._get_gridfs(path)
        try:
            gridfs.delete(gridfs.get_last_version(filename=filename).__getattribute__('_id'))
        except NoFile:
            pass

    def exists(self, path):
        """
        Returns `True` if the file at `path` exists in GridFS.
        """
        gridfs, filename = self._get_gridfs(path)
        return gridfs.exists(filename=filename)

    def listdir(self, path):
        """
        Returns a tuple (folders, lists) that are contained in the
        folder `path`.
        """
        gridfs, filename = self._get_gridfs(path)
        assert not filename
        subcollections = _get_subcollections(gridfs.__getattribute__('__collection'))
        return set(c.split('.')[-1] for c in subcollections), gridfs.list()

    def size(self, path):
        """
        Returns the size of the file at `path`.
        """
        gridfs, filename = self._get_gridfs(path)
        return gridfs.get_last_version(filename=filename).length

    def url(self, name):
        if self.base_url is None:
            raise ValueError("This file is not accessible via a URL.")
        gridfs, filename = self._get_gridfs(name)
        try:
            file_oid = gridfs.get_last_version(filename=filename).__getattr__('_id')
        except NoFile:
            # In case not found by filename
            try:
                # Check is a valid ObjectId
                file_oid = ObjectId(name)
            except (InvalidId, TypeError, ValueError):
                return None
            # Check if exist a file with that ObjectId
            if not gridfs.exists(file_oid):
                return None
        return urljoin(self.base_url, filepath_to_uri(str(file_oid)))

    def created_time(self, path):
        """
        Returns the datetime the file at `path` was created.
        """
        gridfs, filename = self._get_gridfs(path)
        return gridfs.get_last_version(filename=filename).upload_date

    def _get_gridfs(self, path):
        """
        Returns a :class:`~gridfs.GridFS` using the sub-collection for
        `path`.
        """
        path, filename = os.path.split(path)
        path = os.path.join(self.collection, self.location, path.strip(os.sep))
        collection_name = path.replace(os.sep, '.').strip('.')

        if not hasattr(self, '_db'):
            from django.db import connections
            self._db = connections[self.database].connection

        return GridFS(self._db, collection_name), filename

    def get_accessed_time(self, name):
        pass

    def get_created_time(self, name):
        pass

    def get_modified_time(self, name):
        pass

    def path(self, name):
        pass
