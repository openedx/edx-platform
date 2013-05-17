"""
Created on Mar 13, 2013

@author: dmitchell
"""
from __future__ import absolute_import
import re
import logging
from abc import ABCMeta, abstractmethod
from urllib import quote

from bson.objectid import ObjectId
from bson.errors import InvalidId

from xmodule.modulestore.exceptions import InvalidLocationError, \
    InsufficientSpecificationError, OverSpecificationError

from .parsers import parse_url, parse_guid, parse_course_id, parse_block_ref

log = logging.getLogger(__name__)


class Locator(object):
    """
    A locator is like a URL, it refers to a course resource.
    
    Locator is an abstract base class: do not instantiate
    """

    __metaclass__ = ABCMeta 

    @abstractmethod
    def url(self):
        """
        Return a string containing the URL for this location. Raises
        InsufficientSpecificationError if the instance doesn't have a
        complete enough specification to generate a url
        """
        raise InsufficientSpecificationError()


    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        try:
            return self.url()
        except Exception, e:
            return "<@%s:%s>" % (self.__class__.__name__, e.message)


class CourseLocator(Locator):
    """
    Examples of valid CourseLocator specifications:
     CourseLocator(version_guid=ObjectId('519665f6223ebd6980884f2b'))
     CourseLocator(course_id='edu.mit.eecs.6002x')
     CourseLocator(course_id='edu.mit.eecs.6002x;published')
     CourseLocator(course_id='edu.mit.eecs.6002x', revision='published')
     CourseLocator(url='edx://@519665f6223ebd6980884f2b')
     CourseLocator(url='edx://edu.mit.eecs.6002x')
     CourseLocator(url='edx://edu.mit.eecs.6002x;published')
     
    Should have at lease a specific course_id (id for the course as if it were a project w/
    versions) with optional 'revision' (must be 'draft', 'published', or None),
    or version_guid (which points to a specific version). Can contain both in which case
    the persistence layer may raise exceptions if the given version != the current such version
    of the course.
    """

    # Default values
    version_guid = None
    course_id = None
    revision = None

    def __repr__(self):
        """
        Return a string representing this location.
        """
        if self.version_guid:
            return '@' + str(self.version_guid)
        else: 
            result = self.course_id
            if self.revision:
                result += ';' + self.revision
            return result

    def url(self):
        """
        Return a string containing the URL for this location.
        """
        return 'edx://' + quote(str(self), '@;#')
        

    def validate_args (self, url, version_guid, course_id, revision):
        """
        Validate provided arguments.
        """
        args = [arg for arg in [url, version_guid, course_id, revision] if arg]
        if len(args)>2:
            raise OverSpecificationError()
        if len(args)>1 and (url or version_guid):
            raise OverSpecificationError()
        if len(args)==2 and (course_id is None or revision is None):
            raise OverSpecificationError()
        if len(args)==0:
            raise InsufficientSpecificationError()


    def __init__(self, url=None, version_guid=None, course_id=None, revision=None):
        """
        Construct a CourseLocator
        Keyword arguments are mostly exclusive.
        Caller may provide url (but no other parameters).
        Caller may provide version_guid (but no other parameters).
        Caller may provide course_id (optionally provide revision).

        Resulting CourseLocator will have either a version_guid property
        or a course_id (with optional revision) property.

        version_guid must be an instance of bson.objectid.ObjectId or None
        url, course_id, and revision must be strings or None
        
        """
        self.validate_args(url, version_guid, course_id, revision)
        if url:
            self.init_from_url(url)
        elif version_guid:
            self.init_from_version_guid(version_guid)
        elif course_id:
            self.init_from_course_id(course_id, revision)
        assert self.version_guid or self.course_id, \
               "Either version_guid or course_id should be set."
        assert (self.version_guid and not self.course_id) or \
               (not self.version_guid and self.course_id), \
               "Either version_guid or course_id (but not both) should be set"
        

    def init_from_url(self, url):
        """
        url must be a string beginning with 'edx://' and containing
        either a valid version_guid or course_id (with optional revision)
        If a block ('#HW3') is present, it is ignored.
        """
        assert isinstance(url, basestring), \
               '%s is not an instance of basestring' % url
        parse = parse_url(url)
        assert parse, 'Could not parse "%s" as a url' % url
        if parse.has_key('version_guid'):
            try:
                self.version_guid = ObjectId(parse['version_guid'])
            except InvalidId:
                raise ValueError(
                    'The URL "%s" does not contain a valid version_guid' %
                    parse['version_guid'])
        else:
            self.course_id = parse['id']
            self.revision = parse['revision']


    def init_from_version_guid(self, version_guid):
        """
        version_guid must be ain instance of bson.objectid.ObjectId
        """
        assert isinstance(version_guid, ObjectId), \
               '%s is not an instance of ObjectId' % version_guid
        self.version_guid = version_guid

    def init_from_course_id(self, course_id, revision=None):
        """
        Course_id is a string like 'edu.mit.eecs.6002x' or 'edu.mit.eecs.6002x;published'.
        Revision (optional) is a string like 'published'.
        If revision is part of course_id, parse it out separately.
        If a block ('#HW3') is a part of course_id, it is ignored.
        
        """
        parse = parse_course_id(course_id)
        assert parse, 'Could not parse "%s" as a course_id' % course_id
        rev = parse['revision']
        if revision:
            if rev and revision != rev:
                raise OverSpecificationError('Revision cannot be both %s and %s' % (rev, revision))
            self.revision = revision
        else:
            self.revision = rev
        self.course_id = parse['id']


class BlockUsageLocator(CourseLocator):
    """
    Encodes a location.

    Locations address modules (aka blocks) which are definitions situated in a
    course instance. Thus, a Location must identify the course and the occurrence of
    the defined element in the course. Courses can be a version of an offering, the
    current draft head, or the current production version.

    Locators can contain both a version and a course_id w/ revision. The split mongo functions
    may raise errors if these conflict w/ the current db state (i.e., the course's revision !=
    the version_guid)

    Locations can express as urls as well as dictionaries. They consist of
        course_identifier: course_guid | version_guid
        block : guid
        revision : 'draft' | 'published' (optional)
    """
    
    # Default value
    usage_id = None

    def __init__(self, url=None, version_guid=None, course_id=None,
                 revision=None, usage_id=None):
        """
        Construct a BlockUsageLocator
        Keyword arguments are mostly exclusive.
        Caller may provide url (but no other parameters).
        Caller may provide version_guid (but no other parameters).
        Caller may provide course_id (optionally provide revision).
        If course_id is provided, then usage_id is either part of course_id
        or provided separately.

        Resulting BlockUsageLocator will have a usage_id property.
        It will have either a version_guid property
        or a course_id (with optional revision) property.

        version_guid must be an instance of bson.objectid.ObjectId or None
        url, course_id, revision, and usage_id must be strings or None

        """
        self.validate_args(url, version_guid, course_id, revision)
        if url:
            self.init_block_ref_from_url(url)
        if course_id:
            assert url == None, "Cannot specify both url and course_id"
            self.init_block_ref_from_course_id(course_id)
        if version_guid:
            assert url == None, "Cannot specify both url and version_guid"
        if usage_id:
            self.init_block_ref(usage_id)
        CourseLocator.__init__(self, url=url,
                                     version_guid=version_guid,
                                     course_id=course_id,
                                     revision=revision)
        assert self.usage_id, "usage_id should not be None"

    def init_block_ref(self, block_ref):
        parse = parse_block_ref(block_ref)
        assert parse, 'Could not parse "%s" as a block_ref' % block_ref
        self.usage_id = parse['block']

    def init_block_ref_from_url(self, url):
        parse = parse_url(url)
        assert parse, 'Could not parse "%s" as a url' % url
        block = parse['block']
        assert block, 'Could not parse a block reference from url: "%s"' % url
        self.usage_id = block

    def init_block_ref_from_course_id(self, course_id):
        parse = parse_course_id(course_id)
        assert parse, 'Could not parse "%s" as a course_id' % course_id
        block = parse['block']
        assert block, 'Could not parse a block reference from course_id: "%s"' % course_id
        self.usage_id = block


    """ TODO: in progress
    def validate_args(url, version_guid, course_id, revision, block_ref):
        CourseLocator.validate_args(url, version_guid, course_id, revision)
    """

    def __repr__(self):
        """
        Return a string representing this location.
        """
        rep = CourseLocator.__repr__(self)
        if self.version_guid:
            return rep
        else: 
            return rep + '#' + self.usage_id


class DescriptionLocator(Locator):
    """
    Container for how to locate a description
    """
    DESCRIPTION_TAG = 'dx'

    def __init__(self, def_id):
        self.def_id = def_id

    def url(self):
        return self.DESCRIPTION_TAG + '/' + self.def_id

    def version(self):
        return self.def_id


class VersionTree(object):
    """
    Holds trees of Locators to represent version histories.
    """
    def __init__(self, locator, tree_dict=None):
        """
        :param locator: must be version specific (Course has version_guid or definition had id)
        """
        self.locator = locator
        if tree_dict is None:
            self.children = []
        else:
            self.children = [VersionTree(child, tree_dict)
                for child in tree_dict.get(locator.version(), [])]

