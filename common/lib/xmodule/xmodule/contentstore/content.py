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
        raise NotImplementedError
