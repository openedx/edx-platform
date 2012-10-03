from bson.son import SON
from pymongo import Connection
import gridfs
from gridfs.errors import NoFile

from xmodule.modulestore.mongo import location_to_query, Location
from xmodule.contentstore.content import XASSET_LOCATION_TAG

import sys
import logging

from .content import StaticContent, ContentStore
from xmodule.exceptions import NotFoundError


class MongoContentStore(ContentStore):
    def __init__(self, host, db, port=27017):
        logging.debug( 'Using MongoDB for static content serving at host={0} db={1}'.format(host,db))
        _db = Connection(host=host, port=port)[db]
        self.fs = gridfs.GridFS(_db)
        self.fs_files = _db["fs.files"] # the underlying collection GridFS uses


    def save(self, content):
        id = content.get_id()

        # Seems like with the GridFS we can't update existing ID's we have to do a delete/add pair
        if self.fs.exists({"_id" : id}):
            self.fs.delete(id)

        with self.fs.new_file(_id = id, content_type=content.content_type, displayname=content.name) as fp:
            fp.write(content.data)
            return content
        
    
    def find(self, location):
        id = StaticContent.get_id_from_location(location)
        try:
            with self.fs.get(id) as fp:
                return StaticContent(location, fp.displayname, fp.content_type, fp.read(), fp.uploadDate)
        except NoFile:
            raise NotFoundError()

    def get_all_content_info_for_course(self, location):
        course_filter = Location(XASSET_LOCATION_TAG, category="asset",course=location.course,org=location.org)
        # 'borrow' the function 'location_to_query' from the Mongo modulestore implementation
        items = self.fs_files.find(location_to_query(course_filter))
        return items


        
