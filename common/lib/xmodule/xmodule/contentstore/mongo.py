from pymongo import Connection
import gridfs
from gridfs.errors import NoFile

from xmodule.modulestore.mongo import location_to_query, Location
from xmodule.contentstore.content import XASSET_LOCATION_TAG

import logging

from .content import StaticContent, ContentStore
from xmodule.exceptions import NotFoundError
from fs.osfs import OSFS
import os


class MongoContentStore(ContentStore):
    def __init__(self, host, db, port=27017, user=None, password=None, bucket='fs', **kwargs):
        logging.debug('Using MongoDB for static content serving at host={0} db={1}'.format(host, db))
        _db = Connection(host=host, port=port, **kwargs)[db]

        if user is not None and password is not None:
            _db.authenticate(user, password)

        self.fs = gridfs.GridFS(_db, bucket)

        self.fs_files = _db[bucket + ".files"]   # the underlying collection GridFS uses

    def save(self, content):
        id = content.get_id()

        # Seems like with the GridFS we can't update existing ID's we have to do a delete/add pair
        self.delete(id)

        with self.fs.new_file(_id=id, filename=content.get_url_path(), content_type=content.content_type,
                              displayname=content.name, thumbnail_location=content.thumbnail_location,
                              import_path=content.import_path) as fp:

            fp.write(content.data)

        return content

    def delete(self, id):
        if self.fs.exists({"_id": id}):
            self.fs.delete(id)

    def find(self, location, throw_on_not_found=True):
        id = StaticContent.get_id_from_location(location)
        try:
            with self.fs.get(id) as fp:
                return StaticContent(location, fp.displayname, fp.content_type, fp.read(),
                                     fp.uploadDate,
                                     thumbnail_location=fp.thumbnail_location if hasattr(fp, 'thumbnail_location') else None,
                                     import_path=fp.import_path if hasattr(fp, 'import_path') else None)
        except NoFile:
            if throw_on_not_found:
                raise NotFoundError()
            else:
                return None

    def export(self, location, output_directory):
        content = self.find(location)

        if content.import_path is not None:
            output_directory = output_directory + '/' + os.path.dirname(content.import_path)

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        disk_fs = OSFS(output_directory)

        with disk_fs.open(content.name, 'wb') as asset_file:
            asset_file.write(content.data)

    def export_all_for_course(self, course_location, output_directory):
        assets = self.get_all_content_for_course(course_location)

        for asset in assets:
            asset_location = Location(asset['_id'])
            self.export(asset_location, output_directory)

    def get_all_content_thumbnails_for_course(self, location):
        return self._get_all_content_for_course(location, get_thumbnails=True)

    def get_all_content_for_course(self, location):
        return self._get_all_content_for_course(location, get_thumbnails=False)

    def _get_all_content_for_course(self, location, get_thumbnails=False):
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
        course_filter = Location(XASSET_LOCATION_TAG, category="asset" if not get_thumbnails else "thumbnail",
                                 course=location.course, org=location.org)
        # 'borrow' the function 'location_to_query' from the Mongo modulestore implementation
        items = self.fs_files.find(location_to_query(course_filter))
        return list(items)
