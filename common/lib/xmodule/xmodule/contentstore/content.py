XASSET_LOCATION_TAG = 'c4x'
XASSET_SRCREF_PREFIX = 'xasset:'

XASSET_THUMBNAIL_TAIL_NAME = '.jpg'

import os
import logging
import StringIO

from xmodule.modulestore import Location
from .django import contentstore
from PIL import Image

class StaticContent(object):
    def __init__(self, loc, name, content_type, data, last_modified_at=None, thumbnail_location=None):
        self.location = loc
        self.name = name #a display string which can be edited, and thus not part of the location which needs to be fixed
        self.content_type = content_type
        self.data = data
        self.last_modified_at = last_modified_at
        self.thumbnail_location = thumbnail_location

    @property
    def is_thumbnail(self):
        return self.location.category == 'thumbnail'

    @staticmethod
    def generate_thumbnail_name(original_name):
        return ('{0}'+XASSET_THUMBNAIL_TAIL_NAME).format(os.path.splitext(original_name)[0])

    @staticmethod
    def compute_location(org, course, name, revision=None, is_thumbnail=False):
        name = name.replace('/', '_')
        return Location([XASSET_LOCATION_TAG, org, course, 'asset' if not is_thumbnail else 'thumbnail', Location.clean(name), revision])

    def get_id(self):
        return StaticContent.get_id_from_location(self.location)

    def get_url_path(self):
        return StaticContent.get_url_path_from_location(self.location)
    
    @staticmethod
    def get_url_path_from_location(location):
        if location is not None:
            return "/{tag}/{org}/{course}/{category}/{name}".format(**location.dict())
        else:
            return None

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

    def generate_thumbnail(self, content):
        thumbnail_content = None
        # if we're uploading an image, then let's generate a thumbnail so that we can
        # serve it up when needed without having to rescale on the fly
        if content.content_type is not None and content.content_type.split('/')[0] == 'image':
            try:
                # use PIL to do the thumbnail generation (http://www.pythonware.com/products/pil/)
                # My understanding is that PIL will maintain aspect ratios while restricting
                # the max-height/width to be whatever you pass in as 'size'
                # @todo: move the thumbnail size to a configuration setting?!?
                im = Image.open(StringIO.StringIO(content.data))

                # I've seen some exceptions from the PIL library when trying to save palletted 
                # PNG files to JPEG. Per the google-universe, they suggest converting to RGB first.
                im = im.convert('RGB')
                size = 128, 128
                im.thumbnail(size, Image.ANTIALIAS)
                thumbnail_file = StringIO.StringIO()
                im.save(thumbnail_file, 'JPEG')
                thumbnail_file.seek(0)
            
                # use a naming convention to associate originals with the thumbnail
                thumbnail_name = StaticContent.generate_thumbnail_name(content.location.name)

                # then just store this thumbnail as any other piece of content
                thumbnail_file_location = StaticContent.compute_location(content.location.org, content.location.course, 
                                                                                  thumbnail_name, is_thumbnail = True)
                thumbnail_content = StaticContent(thumbnail_file_location, thumbnail_name, 
                                                  'image/jpeg', thumbnail_file)

                contentstore().save(thumbnail_content)
            except:
                raise

        return thumbnail_content




