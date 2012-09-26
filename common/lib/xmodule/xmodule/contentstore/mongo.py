from pymongo import Connection
import gridfs
from gridfs.errors import NoFile

import sys
import logging

from . import StaticContent
from xmodule.exceptions import NotFoundError


class MongoContentStore(object):
    def __init__(self, host, db, port=27017):
        logging.debug( 'Using MongoDB for static content serving at host={0} db={1}'.format(host,db))
        _db = Connection(host=host, port=port)[db]
        self.fs = gridfs.GridFS(_db)

    def update(self, content):
        with self.fs.new_file(filename=content.filename, content_type=content.content_type, displayname=content.name) as fp:
            fp.write(content.data)
            return content
    
    def find(self, filename):
        try:
            with self.fs.get_last_version(filename) as fp:
                return StaticContent(fp.filename, fp.displayname, fp.content_type, fp.read(), fp.uploadDate)
        except NoFile:
            raise NotFoundError()


        
