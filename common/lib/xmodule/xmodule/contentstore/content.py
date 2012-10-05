XASSET_LOCATION_TAG = 'c4x'
XASSET_SRCREF_PREFIX = 'xasset:'

XASSET_THUMBNAIL_TAIL_NAME = '.thumbnail.jpg'

import os
import logging
from xmodule.modulestore import Location

class StaticContent(object):
    def __init__(self, loc, name, content_type, data, last_modified_at=None):
        self.location = loc
        self.name = name #a display string which can be edited, and thus not part of the location which needs to be fixed
        self.content_type = content_type
        self.data = data
        self.last_modified_at = last_modified_at

    @property
    def is_thumbnail(self):
        return self.name.endswith(XASSET_THUMBNAIL_TAIL_NAME)

    def generate_thumbnail_name(self):
        return ('{0}'+XASSET_THUMBNAIL_TAIL_NAME).format(os.path.splitext(self.name)[0])

    @staticmethod
    def compute_location(org, course, name, revision=None):
        return Location([XASSET_LOCATION_TAG, org, course, 'asset', Location.clean(name), revision])

    def get_id(self):
        return StaticContent.get_id_from_location(self.location)

    def get_url_path(self):
        return StaticContent.get_url_path_from_location(self.location)
    
    @staticmethod
    def get_url_path_from_location(location):
        return "/{tag}/{org}/{course}/{category}/{name}".format(**location.dict())

    @staticmethod
    def get_id_from_location(location):
        return { 'tag':location.tag, 'org' : location.org, 'course' : location.course,
                   'category' : location.category, 'name' : location.name, 
                   'revision' : location.revision}
    @staticmethod
    def get_location_from_path(path):
        # remove leading / character if it is there one
        if path.startswith('/'):
            path = path[1:]
        
        return Location(path.split('/'))

    @staticmethod
    def get_id_from_path(path):
        return get_id_from_location(get_location_from_path(path))
    

class ContentStore(object):
    '''
    Abstraction for all ContentStore providers (e.g. MongoDB)
    '''
    def save(self, content):
        raise NotImplementedError

    def find(self, filename):
        raise NotImplementedError

    def get_all_content_for_course(self, location):
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
        raise NotImplementedError
