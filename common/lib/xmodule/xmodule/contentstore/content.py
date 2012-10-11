XASSET_LOCATION_TAG = 'c4x'
XASSET_SRCREF_PREFIX = 'xasset:'

XASSET_THUMBNAIL_TAIL_NAME = '.thumbnail.jpg'

import os
import logging
import StringIO

from xmodule.modulestore import Location
from .django import contentstore
from PIL import Image

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
        # replace some illegal characters
        # for example, when importing courseware static assets, typically the source repository has subdirectories. 
        # right now the content store does not support a hierarchy structure, so collapse those subpaths
        name = name.replace('/', '_')
        return Location([XASSET_LOCATION_TAG, org, course, 'asset', name, revision])

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
                thumbnail_name = content.generate_thumbnail_name()

                # then just store this thumbnail as any other piece of content
                thumbnail_file_location = StaticContent.compute_location(content.location.org, content.location.course, 
                                                                                  thumbnail_name)
                thumbnail_content = StaticContent(thumbnail_file_location, thumbnail_name, 
                                                  'image/jpeg', thumbnail_file)

                contentstore().save(thumbnail_content)
            except:
                raise

        return thumbnail_content




