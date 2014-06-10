import pymongo
import gridfs
from gridfs.errors import NoFile

from xmodule.modulestore.mongo.base import location_to_query, MongoModuleStore
from xmodule.contentstore.content import XASSET_LOCATION_TAG

import logging

from .content import StaticContent, ContentStore, StaticContentStream
from xmodule.exceptions import NotFoundError
from fs.osfs import OSFS
import os
import json
import bson.son
from bson.son import SON
from opaque_keys.edx.locations import AssetLocation


class MongoContentStore(ContentStore):
    # pylint: disable=W0613
    def __init__(self, host, db, port=27017, user=None, password=None, bucket='fs', collection=None, **kwargs):
        """
        Establish the connection with the mongo backend and connect to the collections

        :param collection: ignores but provided for consistency w/ other doc_store_config patterns
        """
        logging.debug('Using MongoDB for static content serving at host={0} db={1}'.format(host, db))
        _db = pymongo.database.Database(
            pymongo.MongoClient(
                host=host,
                port=port,
                document_class=dict,
                **kwargs
            ),
            db
        )

        if user is not None and password is not None:
            _db.authenticate(user, password)

        self.fs = gridfs.GridFS(_db, bucket)

        self.fs_files = _db[bucket + ".files"]  # the underlying collection GridFS uses

    def save(self, content):
        content_id = self.asset_db_key(content.location)

        # Seems like with the GridFS we can't update existing ID's we have to do a delete/add pair
        self.delete(content_id)

        thumbnail_location = content.thumbnail_location.to_deprecated_list_repr() if content.thumbnail_location else None
        with self.fs.new_file(_id=content_id, filename=content.get_url_path(), content_type=content.content_type,
                              displayname=content.name,
                              thumbnail_location=thumbnail_location,
                              import_path=content.import_path,
                              # getattr b/c caching may mean some pickled instances don't have attr
                              locked=getattr(content, 'locked', False)) as fp:
            if hasattr(content.data, '__iter__'):
                for chunk in content.data:
                    fp.write(chunk)
            else:
                fp.write(content.data)

        return content

    def delete(self, location_or_id):
        if isinstance(location_or_id, AssetLocation):
            location_or_id = self.asset_db_key(location_or_id)
        if self.fs.exists({"_id": location_or_id}):
            self.fs.delete(location_or_id)

    def find(self, location, throw_on_not_found=True, as_stream=False):
        content_id = self.asset_db_key(location)

        try:
            if as_stream:
                fp = self.fs.get(content_id)
                thumbnail_location = getattr(fp, 'thumbnail_location', None)
                if thumbnail_location:
                    thumbnail_location = location.course_key.make_asset_key('thumbnail', thumbnail_location[4])
                return StaticContentStream(
                    location, fp.displayname, fp.content_type, fp, last_modified_at=fp.uploadDate,
                    thumbnail_location=thumbnail_location,
                    import_path=getattr(fp, 'import_path', None),
                    length=fp.length, locked=getattr(fp, 'locked', False)
                )
            else:
                with self.fs.get(content_id) as fp:
                    thumbnail_location = getattr(fp, 'thumbnail_location', None)
                    if thumbnail_location:
                        thumbnail_location = location.course_key.make_asset_key('thumbnail', thumbnail_location[4])
                    return StaticContent(
                        location, fp.displayname, fp.content_type, fp.read(), last_modified_at=fp.uploadDate,
                        thumbnail_location=thumbnail_location,
                        import_path=getattr(fp, 'import_path', None),
                        length=fp.length, locked=getattr(fp, 'locked', False)
                    )
        except NoFile:
            if throw_on_not_found:
                raise NotFoundError(content_id)
            else:
                return None

    def get_stream(self, location):
        content_id = self.asset_db_key(location)
        fs_pointer = self.fs_files.find_one({'_id': content_id}, fields={'_id': 1})

        try:
            handle = self.fs.get(fs_pointer['_id'])
        except NoFile:
            raise NotFoundError()

        return handle

    def close_stream(self, handle):
        try:
            handle.close()
        except Exception:  # pylint: disable=broad-except
            pass

    def export(self, location, output_directory):
        content = self.find(location)

        if content.import_path is not None:
            output_directory = output_directory + '/' + os.path.dirname(content.import_path)

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        disk_fs = OSFS(output_directory)

        with disk_fs.open(content.name, 'wb') as asset_file:
            asset_file.write(content.data)

    def export_all_for_course(self, course_key, output_directory, assets_policy_file):
        """
        Export all of this course's assets to the output_directory. Export all of the assets'
        attributes to the policy file.

        Args:
            course_key (CourseKey): the :class:`CourseKey` identifying the course
            output_directory: the directory under which to put all the asset files
            assets_policy_file: the filename for the policy file which should be in the same
                directory as the other policy files.
        """
        policy = {}
        assets, __ = self.get_all_content_for_course(course_key)

        for asset in assets:
            asset_location = AssetLocation._from_deprecated_son(asset['_id'], course_key.run)  # pylint: disable=protected-access
            self.export(asset_location, output_directory)
            for attr, value in asset.iteritems():
                if attr not in ['_id', 'md5', 'uploadDate', 'length', 'chunkSize']:
                    policy.setdefault(asset_location.name, {})[attr] = value

        with open(assets_policy_file, 'w') as f:
            json.dump(policy, f)

    def get_all_content_thumbnails_for_course(self, course_key):
        return self._get_all_content_for_course(course_key, get_thumbnails=True)[0]

    def get_all_content_for_course(self, course_key, start=0, maxresults=-1, sort=None):
        return self._get_all_content_for_course(
            course_key, start=start, maxresults=maxresults, get_thumbnails=False, sort=sort
        )

    def _get_all_content_for_course(self, course_key, get_thumbnails=False, start=0, maxresults=-1, sort=None):
        '''
        Returns a list of all static assets for a course. The return format is a list of dictionary elements. Example:

            [

            {u'displayname': u'profile.jpg', u'chunkSize': 262144, u'length': 85374,
            u'uploadDate': datetime.datetime(2012, 10, 3, 5, 41, 54, 183000), u'contentType': u'image/jpeg',
            u'_id': {u'category': u'asset', u'name': u'profile.jpg', u'course': u'6.002x', u'tag': u'c4x',
            u'org': u'MITx', u'revision': None}, u'md5': u'36dc53519d4b735eb6beba51cd686a0e'},

            {u'displayname': u'profile.thumbnail.jpg', u'chunkSize': 262144, u'length': 4073,
            u'uploadDate': datetime.datetime(2012, 10, 3, 5, 41, 54, 196000), u'contentType': u'image/jpeg',
            u'_id': {u'category': u'asset', u'name': u'profile.thumbnail.jpg', u'course': u'6.002x', u'tag': u'c4x',
            u'org': u'MITx', u'revision': None}, u'md5': u'ff1532598830e3feac91c2449eaa60d6'},

            ....

            ]
        '''
        course_filter = course_key.make_asset_key(
            "asset" if not get_thumbnails else "thumbnail",
            None
        )
        # 'borrow' the function 'location_to_query' from the Mongo modulestore implementation
        if maxresults > 0:
            items = self.fs_files.find(
                location_to_query(course_filter, wildcard=True, tag=XASSET_LOCATION_TAG),
                skip=start, limit=maxresults, sort=sort
            )
        else:
            items = self.fs_files.find(location_to_query(course_filter, wildcard=True, tag=XASSET_LOCATION_TAG), sort=sort)
        count = items.count()
        return list(items), count

    def set_attr(self, asset_key, attr, value=True):
        """
        Add/set the given attr on the asset at the given location. Does not allow overwriting gridFS built in
        attrs such as _id, md5, uploadDate, length. Value can be any type which pymongo accepts.

        Returns nothing

        Raises NotFoundError if no such item exists
        Raises AttributeError is attr is one of the build in attrs.

        :param asset_key: an AssetKey
        :param attr: which attribute to set
        :param value: the value to set it to (any type pymongo accepts such as datetime, number, string)
        """
        self.set_attrs(asset_key, {attr: value})

    def get_attr(self, location, attr, default=None):
        """
        Get the value of attr set on location. If attr is unset, it returns default. Unlike set, this accessor
        does allow getting the value of reserved keywords.
        :param location: a c4x asset location
        """
        return self.get_attrs(location).get(attr, default)

    def set_attrs(self, location, attr_dict):
        """
        Like set_attr but sets multiple key value pairs.

        Returns nothing.

        Raises NotFoundError if no such item exists
        Raises AttributeError is attr_dict has any attrs which are one of the build in attrs.

        :param location:  a c4x asset location
        """
        for attr in attr_dict.iterkeys():
            if attr in ['_id', 'md5', 'uploadDate', 'length']:
                raise AttributeError("{} is a protected attribute.".format(attr))
        asset_db_key = self.asset_db_key(location)
        # FIXME remove fetch and use a form of update which fails if doesn't exist
        item = self.fs_files.find_one({'_id': asset_db_key})
        if item is None:
            raise NotFoundError(asset_db_key)
        self.fs_files.update({'_id': asset_db_key}, {"$set": attr_dict})

    def get_attrs(self, location):
        """
        Gets all of the attributes associated with the given asset. Note, returns even built in attrs
        such as md5 which you cannot resubmit in an update; so, don't call set_attrs with the result of this
        but only with the set of attrs you want to explicitly update.

        The attrs will be a superset of _id, contentType, chunkSize, filename, uploadDate, & md5

        :param location: a c4x asset location
        """
        asset_db_key = self.asset_db_key(location)
        item = self.fs_files.find_one({'_id': asset_db_key})
        if item is None:
            raise NotFoundError(asset_db_key)
        return item

    def delete_all_course_assets(self, course_key):
        """
        Delete all assets identified via this course_key. Dangerous operation which may remove assets
        referenced by other runs or other courses.
        :param course_key:
        """
        course_query = MongoModuleStore._course_key_to_son(course_key, tag=XASSET_LOCATION_TAG)  # pylint: disable=protected-access
        matching_assets = self.fs_files.find(course_query)
        for asset in matching_assets:
            self.fs.delete(asset['_id'])

    @staticmethod
    def asset_db_key(location):
        """
        Returns the database query to find the given asset location.
        """
        # codifying the original order which pymongo used for the dicts coming out of location_to_dict
        # stability of order is more important than sanity of order as any changes to order make things
        # unfindable
        ordered_key_fields = ['category', 'name', 'course', 'tag', 'org', 'revision']
        return SON((field_name, getattr(location, field_name)) for field_name in ordered_key_fields)
