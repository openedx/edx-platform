import re
import uuid
XASSET_LOCATION_TAG = 'c4x'
XASSET_SRCREF_PREFIX = 'xasset:'

XASSET_THUMBNAIL_TAIL_NAME = '.jpg'

STREAM_DATA_CHUNK_SIZE = 1024

import os
import logging
import StringIO
from urlparse import urlparse, urlunparse, parse_qsl
from urllib import urlencode

from opaque_keys.edx.locator import AssetLocator
from opaque_keys.edx.keys import CourseKey, AssetKey
from opaque_keys import InvalidKeyError
from PIL import Image


class StaticContent(object):
    def __init__(self, loc, name, content_type, data, last_modified_at=None, thumbnail_location=None, import_path=None,
                 length=None, locked=False):
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

    @property
    def is_thumbnail(self):
        return self.location.category == 'thumbnail'

    @staticmethod
    def generate_thumbnail_name(original_name):
        name_root, ext = os.path.splitext(original_name)
        if not ext == XASSET_THUMBNAIL_TAIL_NAME:
            name_root = name_root + ext.replace(u'.', u'-')
        return u"{name_root}{extension}".format(
            name_root=name_root,
            extension=XASSET_THUMBNAIL_TAIL_NAME,)

    @staticmethod
    def compute_location(course_key, path, revision=None, is_thumbnail=False):
        """
        Constructs a location object for static content.

        - course_key: the course that this asset belongs to
        - path: is the name of the static asset
        - revision: is the object's revision information
        - is_thumbnail: is whether or not we want the thumbnail version of this
            asset
        """
        path = path.replace('/', '_')
        return course_key.make_asset_key(
            'asset' if not is_thumbnail else 'thumbnail',
            AssetLocator.clean_keeping_underscores(path)
        ).for_branch(None)

    def get_id(self):
        return self.location

    @property
    def data(self):
        return self._data

    ASSET_URL_RE = re.compile(r"""
        /?c4x/
        (?P<org>[^/]+)/
        (?P<course>[^/]+)/
        (?P<category>[^/]+)/
        (?P<name>[^/]+)
    """, re.VERBOSE | re.IGNORECASE)

    @staticmethod
    def is_c4x_path(path_string):
        """
        Returns a boolean if a path is believed to be a c4x link based on the leading element
        """
        return StaticContent.ASSET_URL_RE.match(path_string) is not None

    @staticmethod
    def get_static_path_from_location(location):
        """
        This utility static method will take a location identifier and create a 'durable' /static/.. URL representation of it.
        This link is 'durable' as it can maintain integrity across cloning of courseware across course-ids, e.g. reruns of
        courses.
        In the LMS/CMS, we have runtime link-rewriting, so at render time, this /static/... format will get translated into
        the actual /c4x/... path which the client needs to reference static content
        """
        if location is not None:
            return u"/static/{name}".format(name=location.name)
        else:
            return None

    @staticmethod
    def get_base_url_path_for_course_assets(course_key):
        if course_key is None:
            return None

        assert isinstance(course_key, CourseKey)
        placeholder_id = uuid.uuid4().hex
        # create a dummy asset location with a fake but unique name. strip off the name, and return it
        url_path = StaticContent.serialize_asset_key_with_slash(
            course_key.make_asset_key('asset', placeholder_id).for_branch(None)
        )
        return url_path.replace(placeholder_id, '')

    @staticmethod
    def get_location_from_path(path):
        """
        Generate an AssetKey for the given path (old c4x/org/course/asset/name syntax)
        """
        try:
            return AssetKey.from_string(path)
        except InvalidKeyError:
            # TODO - re-address this once LMS-11198 is tackled.
            if path.startswith('/'):
                # try stripping off the leading slash and try again
                return AssetKey.from_string(path[1:])

    @staticmethod
    def convert_legacy_static_url_with_course_id(path, course_id):
        """
        Returns a path to a piece of static content when we are provided with a filepath and
        a course_id
        """
        # Generate url of urlparse.path component
        scheme, netloc, orig_path, params, query, fragment = urlparse(path)
        loc = StaticContent.compute_location(course_id, orig_path)
        loc_url = StaticContent.serialize_asset_key_with_slash(loc)

        # parse the query params for "^/static/" and replace with the location url
        orig_query = parse_qsl(query)
        new_query_list = []
        for query_name, query_value in orig_query:
            if query_value.startswith("/static/"):
                new_query = StaticContent.compute_location(
                    course_id,
                    query_value[len('/static/'):],
                )
                new_query_url = StaticContent.serialize_asset_key_with_slash(new_query)
                new_query_list.append((query_name, new_query_url))
            else:
                new_query_list.append((query_name, query_value))

        # Reconstruct with new path
        return urlunparse((scheme, netloc, loc_url, params, urlencode(new_query_list), fragment))

    def stream_data(self):
        yield self._data

    @staticmethod
    def serialize_asset_key_with_slash(asset_key):
        """
        Legacy code expects the serialized asset key to start w/ a slash; so, do that in one place
        :param asset_key:
        """
        url = unicode(asset_key)
        if not url.startswith('/'):
            url = '/' + url  # TODO - re-address this once LMS-11198 is tackled.
        return url


class StaticContentStream(StaticContent):
    def __init__(self, loc, name, content_type, stream, last_modified_at=None, thumbnail_location=None, import_path=None,
                 length=None, locked=False):
        super(StaticContentStream, self).__init__(loc, name, content_type, None, last_modified_at=last_modified_at,
                                                  thumbnail_location=thumbnail_location, import_path=import_path,
                                                  length=length, locked=locked)
        self._stream = stream

    def stream_data(self):
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
                                import_path=self.import_path, length=self.length, locked=self.locked)
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

    def generate_thumbnail(self, content, tempfile_path=None):
        thumbnail_content = None
        # use a naming convention to associate originals with the thumbnail
        thumbnail_name = StaticContent.generate_thumbnail_name(content.location.name)

        thumbnail_file_location = StaticContent.compute_location(
            content.location.course_key, thumbnail_name, is_thumbnail=True
        )

        # if we're uploading an image, then let's generate a thumbnail so that we can
        # serve it up when needed without having to rescale on the fly
        if content.content_type is not None and content.content_type.split('/')[0] == 'image':
            try:
                # use PIL to do the thumbnail generation (http://www.pythonware.com/products/pil/)
                # My understanding is that PIL will maintain aspect ratios while restricting
                # the max-height/width to be whatever you pass in as 'size'
                # @todo: move the thumbnail size to a configuration setting?!?
                if tempfile_path is None:
                    im = Image.open(StringIO.StringIO(content.data))
                else:
                    im = Image.open(tempfile_path)

                # I've seen some exceptions from the PIL library when trying to save palletted
                # PNG files to JPEG. Per the google-universe, they suggest converting to RGB first.
                im = im.convert('RGB')
                size = 128, 128
                im.thumbnail(size, Image.ANTIALIAS)
                thumbnail_file = StringIO.StringIO()
                im.save(thumbnail_file, 'JPEG')
                thumbnail_file.seek(0)

                # store this thumbnail as any other piece of content
                thumbnail_content = StaticContent(thumbnail_file_location, thumbnail_name,
                                                  'image/jpeg', thumbnail_file)

                self.save(thumbnail_content)

            except Exception, e:
                # log and continue as thumbnails are generally considered as optional
                logging.exception(u"Failed to generate thumbnail for {0}. Exception: {1}".format(content.location, str(e)))

        return thumbnail_content, thumbnail_file_location

    def ensure_indexes(self):
        """
        Ensure that all appropriate indexes are created that are needed by this modulestore, or raise
        an exception if unable to.
        """
        pass
