import re
import uuid

from xmodule.assetstore.assetmgr import AssetManager

XASSET_LOCATION_TAG = 'c4x'
XASSET_SRCREF_PREFIX = 'xasset:'
XASSET_THUMBNAIL_TAIL_NAME = '.jpg'
STREAM_DATA_CHUNK_SIZE = 1024

import os
import logging
import StringIO
from urlparse import urlparse, urlunparse, parse_qsl
from urllib import urlencode, quote_plus

from opaque_keys.edx.locator import AssetLocator
from opaque_keys.edx.keys import CourseKey, AssetKey
from opaque_keys import InvalidKeyError
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.exceptions import NotFoundError
from PIL import Image


class StaticContent(object):
    def __init__(self, loc, name, content_type, data, last_modified_at=None, thumbnail_location=None, import_path=None,
                 length=None, locked=False, content_digest=None):
        self.location = loc
        self.name = name  # a display string which can be edited, and thus not part of the location which needs to be fixed
        self.content_type = content_type
        self._data = data
        self.length = length
        self.last_modified_at = last_modified_at
        self.thumbnail_location = thumbnail_location
        # optional information about where this file was imported from. This is needed to support import/export
        # cycles
        self.import_path = import_path
        self.locked = locked
        self.content_digest = content_digest

    @property
    def is_thumbnail(self):
        return self.location.category == 'thumbnail'

    @staticmethod
    def compute_location(course_key, path, is_thumbnail=False):
        """
        Constructs a location object for static content.

        - course_key: the course that this asset belongs to
        - path: is the name of the static asset
        - is_thumbnail: is whether or not we want the thumbnail version of this
            asset
        """
        path = path.replace('/', '_')
        return course_key.make_asset_key(
            'asset' if not is_thumbnail else 'thumbnail',
            AssetLocator.clean_keeping_underscores(path)
        ).for_branch(None)

    @staticmethod
    def generate_thumbnail_name(original_name, dimensions=None, extension=None):
        """
        - original_name: Name of the asset (typically its location.name)
        - dimensions: `None` or a tuple of (width, height) in pixels
        - extension: `None` or desired filename extension of the thumbnail
        """
        if extension is None:
            extension = XASSET_THUMBNAIL_TAIL_NAME

        name_root, ext = os.path.splitext(original_name)
        if not ext == extension:
            name_root = name_root + ext.replace(u'.', u'-')

        if dimensions:
            width, height = dimensions  # pylint: disable=unpacking-non-sequence
            name_root += "-{}x{}".format(width, height)

        return u"{name_root}{extension}".format(
            name_root=name_root,
            extension=extension,
        )

    def get_id(self):
        return self.location

    def stream_data(self):
        """
        Streams the data of this content to the caller.
        """
        return self._data

    @property
    def data(self):
        return self._data


class StaticContentStream(StaticContent):
    def __init__(self, loc, name, content_type, stream, last_modified_at=None, thumbnail_location=None, import_path=None,
                 length=None, locked=False, content_digest=None):
        super(StaticContentStream, self).__init__(loc, name, content_type, None, last_modified_at=last_modified_at,
                                                  thumbnail_location=thumbnail_location, import_path=import_path,
                                                  length=length, locked=locked, content_digest=content_digest)
        self._stream = stream

    def stream_data(self):
        """
        Streams the data of this content to the caller.
        """
        while True:
            chunk = self._stream.read(STREAM_DATA_CHUNK_SIZE)
            if len(chunk) == 0:
                break
            yield chunk

    def stream_data_in_range(self, first_byte, last_byte):
        """
        Stream the data between first_byte and last_byte (included)
        """
        self._stream.seek(first_byte)
        position = first_byte
        while True:
            if last_byte < position + STREAM_DATA_CHUNK_SIZE - 1:
                chunk = self._stream.read(last_byte - position + 1)
                yield chunk
                break
            chunk = self._stream.read(STREAM_DATA_CHUNK_SIZE)
            position += STREAM_DATA_CHUNK_SIZE
            yield chunk

    def close(self):
        self._stream.close()

    def copy_to_in_mem(self):
        self._stream.seek(0)
        content = StaticContent(self.location, self.name, self.content_type, self._stream.read(),
                                last_modified_at=self.last_modified_at, thumbnail_location=self.thumbnail_location,
                                import_path=self.import_path, length=self.length, locked=self.locked,
                                content_digest=self.content_digest)
        return content


class ContentStore(object):
    '''
    Abstraction for all ContentStore providers (e.g. MongoDB)
    '''
    def save(self, content):
        raise NotImplementedError

    def find(self, filename):
        raise NotImplementedError

    def get_all_content_for_course(self, course_key, start=0, maxresults=-1, sort=None, filter_params=None):
        '''
        Returns a list of static assets for a course, followed by the total number of assets.
        By default all assets are returned, but start and maxresults can be provided to limit the query.

        The return format is a list of asset data dictionaries.
        The asset data dictionaries have the following keys:
            asset_key (:class:`opaque_keys.edx.AssetKey`): The key of the asset
            displayname: The human-readable name of the asset
            uploadDate (datetime.datetime): The date and time that the file was uploadDate
            contentType: The mimetype string of the asset
            md5: An md5 hash of the asset content
        '''
        raise NotImplementedError

    def delete_all_course_assets(self, course_key):
        """
        Delete all of the assets which use this course_key as an identifier
        :param course_key:
        """
        raise NotImplementedError

    def copy_all_course_assets(self, source_course_key, dest_course_key):
        """
        Copy all the course assets from source_course_key to dest_course_key
        """
        raise NotImplementedError

    def generate_thumbnail(self, content, tempfile_path=None, dimensions=None):
        """Create a thumbnail for a given image.

        Returns a tuple of (StaticContent, AssetKey)

        `content` is the StaticContent representing the image you want to make a
        thumbnail out of.

        `tempfile_path` is a string path to the location of a file to read from
        in order to grab the image data, instead of relying on `content.data`

        `dimensions` is an optional param that represents (width, height) in
        pixels. It defaults to None.
        """
        thumbnail_content = None
        is_svg = content.content_type == 'image/svg+xml'
        # use a naming convention to associate originals with the thumbnail
        thumbnail_name = StaticContent.generate_thumbnail_name(
            content.location.name, dimensions=dimensions, extension='.svg' if is_svg else None
        )
        thumbnail_file_location = StaticContent.compute_location(
            content.location.course_key, thumbnail_name, is_thumbnail=True
        )

        # if we're uploading an image, then let's generate a thumbnail so that we can
        # serve it up when needed without having to rescale on the fly
        try:
            if is_svg:
                # for svg simply store the provided svg file, since vector graphics should be good enough
                # for downscaling client-side
                if tempfile_path is None:
                    thumbnail_file = StringIO.StringIO(content.data)
                else:
                    with open(tempfile_path) as f:
                        thumbnail_file = StringIO.StringIO(f.read())
                thumbnail_content = StaticContent(thumbnail_file_location, thumbnail_name,
                                                  'image/svg+xml', thumbnail_file)
                self.save(thumbnail_content)
            elif content.content_type is not None and content.content_type.split('/')[0] == 'image':
                # use PIL to do the thumbnail generation (http://www.pythonware.com/products/pil/)
                # My understanding is that PIL will maintain aspect ratios while restricting
                # the max-height/width to be whatever you pass in as 'size'
                # @todo: move the thumbnail size to a configuration setting?!?
                if tempfile_path is None:
                    source = StringIO.StringIO(content.data)
                else:
                    source = tempfile_path

                # We use the context manager here to avoid leaking the inner file descriptor
                # of the Image object -- this way it gets closed after we're done with using it.
                thumbnail_file = StringIO.StringIO()
                with Image.open(source) as image:
                    # I've seen some exceptions from the PIL library when trying to save palletted
                    # PNG files to JPEG. Per the google-universe, they suggest converting to RGB first.
                    thumbnail_image = image.convert('RGB')

                    if not dimensions:
                        dimensions = (128, 128)

                    thumbnail_image.thumbnail(dimensions, Image.ANTIALIAS)
                    thumbnail_image.save(thumbnail_file, 'JPEG')
                    thumbnail_file.seek(0)

                # store this thumbnail as any other piece of content
                thumbnail_content = StaticContent(thumbnail_file_location, thumbnail_name,
                                                  'image/jpeg', thumbnail_file)

                self.save(thumbnail_content)

        except Exception, exc:  # pylint: disable=broad-except
            # log and continue as thumbnails are generally considered as optional
            logging.exception(
                u"Failed to generate thumbnail for {0}. Exception: {1}".format(content.location, str(exc))
            )

        return thumbnail_content, thumbnail_file_location

    def ensure_indexes(self):
        """
        Ensure that all appropriate indexes are created that are needed by this modulestore, or raise
        an exception if unable to.
        """
        pass
