"""
Identifier for course resources.
"""

from __future__ import absolute_import
import logging
import inspect
from abc import ABCMeta, abstractmethod
from urllib import quote

from bson.objectid import ObjectId
from bson.errors import InvalidId

from xmodule.modulestore.exceptions import InsufficientSpecificationError, OverSpecificationError

from .parsers import parse_url, parse_course_id, parse_block_ref
from .parsers import BRANCH_PREFIX, BLOCK_PREFIX, URL_VERSION_PREFIX

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
        '''
        repr(self) returns something like this: CourseLocator("mit.eecs.6002x")
        '''
        classname = self.__class__.__name__
        if classname.find('.') != -1:
            classname = classname.split['.'][-1]
        return '%s("%s")' % (classname, unicode(self))

    def __str__(self):
        '''
        str(self) returns something like this: "mit.eecs.6002x"
        '''
        return unicode(self).encode('utf8')

    def __unicode__(self):
        '''
        unicode(self) returns something like this: "mit.eecs.6002x"
        '''
        return self.url()

    @abstractmethod
    def version(self):
        """
        Returns the ObjectId referencing this specific location.
        Raises InsufficientSpecificationError if the instance
        doesn't have a complete enough specification.
        """
        raise InsufficientSpecificationError()

    def set_property(self, property_name, new):
        """
        Initialize property to new value.
        If property has already been initialized to a different value, raise an exception.
        """
        current = getattr(self, property_name)
        if current and current != new:
            raise OverSpecificationError('%s cannot be both %s and %s' %
                                         (property_name, current, new))
        setattr(self, property_name, new)


class CourseLocator(Locator):
    """
    Examples of valid CourseLocator specifications:
     CourseLocator(version_guid=ObjectId('519665f6223ebd6980884f2b'))
     CourseLocator(course_id='mit.eecs.6002x')
     CourseLocator(course_id='mit.eecs.6002x/branch/published')
     CourseLocator(course_id='mit.eecs.6002x', branch='published')
     CourseLocator(url='edx://version/519665f6223ebd6980884f2b')
     CourseLocator(url='edx://mit.eecs.6002x')
     CourseLocator(url='edx://mit.eecs.6002x/branch/published')
     CourseLocator(url='edx://mit.eecs.6002x/branch/published/version/519665f6223ebd6980884f2b')

    Should have at lease a specific course_id (id for the course as if it were a project w/
    versions) with optional 'branch',
    or version_guid (which points to a specific version). Can contain both in which case
    the persistence layer may raise exceptions if the given version != the current such version
    of the course.
    """

    # Default values
    version_guid = None
    course_id = None
    branch = None

    def __unicode__(self):
        """
        Return a string representing this location.
        """
        if self.course_id:
            result = self.course_id
            if self.branch:
                result += BRANCH_PREFIX + self.branch
            return result
        elif self.version_guid:
            return URL_VERSION_PREFIX + str(self.version_guid)
        else:
            # raise InsufficientSpecificationError("missing course_id or version_guid")
            return '<InsufficientSpecificationError: missing course_id or version_guid>'

    def url(self):
        """
        Return a string containing the URL for this location.
        """
        return 'edx://' + unicode(self)

    # -- unused args which are used via inspect
    # pylint: disable= W0613
    def validate_args(self, url, version_guid, course_id, branch):
        """
        Validate provided arguments.
        """
        need_oneof = set(('url', 'version_guid', 'course_id'))
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        provided_args = [a for a in args if a != 'self' and values[a] is not None]
        if len(need_oneof.intersection(provided_args)) == 0:
            raise InsufficientSpecificationError("Must provide one of these args: %s " %
                                                 list(need_oneof))

    def is_fully_specified(self):
        """
        Returns True if either version_guid is specified, or course_id+branch
        are specified.
        This should always return True, since this should be validated in the constructor.
        """
        return self.version_guid is not None \
            or (self.course_id is not None and self.branch is not None)

    def set_course_id(self, new):
        """
        Initialize course_id to new value.
        If course_id has already been initialized to a different value, raise an exception.
        """
        self.set_property('course_id', new)

    def set_branch(self, new):
        """
        Initialize branch to new value.
        If branch has already been initialized to a different value, raise an exception.
        """
        self.set_property('branch', new)

    def set_version_guid(self, new):
        """
        Initialize version_guid to new value.
        If version_guid has already been initialized to a different value, raise an exception.
        """
        self.set_property('version_guid', new)

    def as_course_locator(self):
        """
        Returns a copy of itself (downcasting) as a CourseLocator.
        The copy has the same CourseLocator fields as the original.
        The copy does not include subclass information, such as
        a usage_id (a property of BlockUsageLocator).
        """
        return CourseLocator(course_id=self.course_id,
                             version_guid=self.version_guid,
                             branch=self.branch)

    def __init__(self, url=None, version_guid=None, course_id=None, branch=None):
        """
        Construct a CourseLocator
        Caller may provide url (but no other parameters).
        Caller may provide version_guid (but no other parameters).
        Caller may provide course_id (optionally provide branch).

        Resulting CourseLocator will have either a version_guid property
        or a course_id (with optional branch) property, or both.

        version_guid must be an instance of bson.objectid.ObjectId or None
        url, course_id, and branch must be strings or None

        """
        self.validate_args(url, version_guid, course_id, branch)
        if url:
            self.init_from_url(url)
        if version_guid:
            self.init_from_version_guid(version_guid)
        if course_id or branch:
            self.init_from_course_id(course_id, branch)
        assert self.version_guid or self.course_id, \
            "Either version_guid or course_id should be set."

    @classmethod
    def as_object_id(cls, value):
        """
        Attempts to cast value as a bson.objectid.ObjectId.
        If cast fails, raises ValueError
        """
        if isinstance(value, ObjectId):
            return value
        try:
            return ObjectId(value)
        except InvalidId:
            raise ValueError('"%s" is not a valid version_guid' % value)

    def init_from_url(self, url):
        """
        url must be a string beginning with 'edx://' and containing
        either a valid version_guid or course_id (with optional branch), or both.
        """
        if isinstance(url, Locator):
            url = url.url()
        assert isinstance(url, basestring), '%s is not an instance of basestring' % url
        parse = parse_url(url)
        assert parse, 'Could not parse "%s" as a url' % url
        self._set_value(
            parse, 'version_guid', lambda (new_guid): self.set_version_guid(self.as_object_id(new_guid))
        )
        self._set_value(parse, 'id', lambda (new_id): self.set_course_id(new_id))
        self._set_value(parse, 'branch', lambda (new_branch): self.set_branch(new_branch))

    def init_from_version_guid(self, version_guid):
        """
        version_guid must be an instance of bson.objectid.ObjectId,
        or able to be cast as one.
        If it's a string, attempt to cast it as an ObjectId first.
        """
        version_guid = self.as_object_id(version_guid)

        assert isinstance(version_guid, ObjectId), \
            '%s is not an instance of ObjectId' % version_guid
        self.set_version_guid(version_guid)

    def init_from_course_id(self, course_id, explicit_branch=None):
        """
        Course_id is a string like 'mit.eecs.6002x' or 'mit.eecs.6002x/branch/published'.

        Revision (optional) is a string like 'published'.
        It may be provided explicitly (explicit_branch) or embedded into course_id.
        If branch is part of course_id (".../branch/published"), parse it out separately.
        If branch is provided both ways, that's ok as long as they are the same value.

        If a block ('/block/HW3') is a part of course_id, it is ignored.

        """

        if course_id:
            if isinstance(course_id, CourseLocator):
                course_id = course_id.course_id
                assert course_id, "%s does not have a valid course_id"

            parse = parse_course_id(course_id)
            assert parse, 'Could not parse "%s" as a course_id' % course_id
            self.set_course_id(parse['id'])
            rev = parse['branch']
            if rev:
                self.set_branch(rev)
        if explicit_branch:
            self.set_branch(explicit_branch)

    def version(self):
        """
        Returns the ObjectId referencing this specific location.
        """
        return self.version_guid

    def html_id(self):
        """
        Generate a discussion group id based on course

        To make compatible with old Location object functionality. I don't believe this behavior fits at this
        place, but I have no way to override. If this is really needed, it should probably use the pretty_id to seed
        the name although that's mutable. We should also clearly define the purpose and restrictions of this
        (e.g., I'm assuming periods are fine).
        """
        return self.course_id

    def _set_value(self, parse, key, setter):
        """
        Helper method that gets a value out of the dict returned by parse,
        and then sets the corresponding bit of information in this locator
        (via the supplied lambda 'setter'), unless the value is None.
        """
        value = parse.get(key, None)
        if value:
            setter(value)


class BlockUsageLocator(CourseLocator):
    """
    Encodes a location.

    Locations address modules (aka blocks) which are definitions situated in a
    course instance. Thus, a Location must identify the course and the occurrence of
    the defined element in the course. Courses can be a version of an offering, the
    current draft head, or the current production version.

    Locators can contain both a version and a course_id w/ branch. The split mongo functions
    may raise errors if these conflict w/ the current db state (i.e., the course's branch !=
    the version_guid)

    Locations can express as urls as well as dictionaries. They consist of
        course_identifier: course_guid | version_guid
        block : guid
        branch : string
    """

    # Default value
    usage_id = None

    def __init__(self, url=None, version_guid=None, course_id=None,
                 branch=None, usage_id=None):
        """
        Construct a BlockUsageLocator
        Caller may provide url, version_guid, or course_id, and optionally provide branch.

        The usage_id may be specified, either explictly or as part of
        the url or course_id. If omitted, the locator is created but it
        has not yet been initialized.

        Resulting BlockUsageLocator will have a usage_id property.
        It will have either a version_guid property or a course_id (with optional branch) property, or both.

        version_guid must be an instance of bson.objectid.ObjectId or None
        url, course_id, branch, and usage_id must be strings or None

        """
        self.validate_args(url, version_guid, course_id, branch)
        if url:
            self.init_block_ref_from_url(url)
        if course_id:
            self.init_block_ref_from_course_id(course_id)
        if usage_id:
            self.init_block_ref(usage_id)
        CourseLocator.__init__(self,
                               url=url,
                               version_guid=version_guid,
                               course_id=course_id,
                               branch=branch)

    def is_initialized(self):
        """
        Returns True if usage_id has been initialized, else returns False
        """
        return self.usage_id is not None

    def version_agnostic(self):
        """
        Returns a copy of itself.
        If both version_guid and course_id are known, use a blank course_id in the copy.

        We don't care if the locator's version is not the current head; so, avoid version conflict
        by reducing info.

        :param block_locator:
        """
        if self.course_id and self.version_guid:
            return BlockUsageLocator(version_guid=self.version_guid,
                                     branch=self.branch,
                                     usage_id=self.usage_id)
        else:
            return BlockUsageLocator(course_id=self.course_id,
                                     branch=self.branch,
                                     usage_id=self.usage_id)

    def set_usage_id(self, new):
        """
        Initialize usage_id to new value.
        If usage_id has already been initialized to a different value, raise an exception.
        """
        self.set_property('usage_id', new)

    def init_block_ref(self, block_ref):
        parse = parse_block_ref(block_ref)
        assert parse, 'Could not parse "%s" as a block_ref' % block_ref
        self.set_usage_id(parse['block'])

    def init_block_ref_from_url(self, url):
        if isinstance(url, Locator):
            url = url.url()
        parse = parse_url(url)
        assert parse, 'Could not parse "%s" as a url' % url
        self._set_value(parse, 'block', lambda(new_block): self.set_usage_id(new_block))

    def init_block_ref_from_course_id(self, course_id):
        if isinstance(course_id, CourseLocator):
            course_id = course_id.course_id
            assert course_id, "%s does not have a valid course_id"
        parse = parse_course_id(course_id)
        assert parse, 'Could not parse "%s" as a course_id' % course_id
        self._set_value(parse, 'block', lambda(new_block): self.set_usage_id(new_block))

    def __unicode__(self):
        """
        Return a string representing this location.
        """
        rep = CourseLocator.__unicode__(self)
        if self.usage_id is None:
            # usage_id has not been initialized
            return rep + BLOCK_PREFIX + 'NONE'
        else:
            return rep + BLOCK_PREFIX + self.usage_id


class DescriptionLocator(Locator):
    """
    Container for how to locate a description (the course-independent content).
    """

    def __init__(self, definition_id):
        self.definition_id = definition_id

    def __unicode__(self):
        '''
        Return a string representing this location.
        unicode(self) returns something like this: "version/519665f6223ebd6980884f2b"
        '''
        return URL_VERSION_PREFIX + str(self.definition_id)

    def url(self):
        """
        Return a string containing the URL for this location.
        url(self) returns something like this: 'edx://version/519665f6223ebd6980884f2b'
        """
        return 'edx://' + unicode(self)

    def version(self):
        """
        Returns the ObjectId referencing this specific location.
        """
        return self.definition_id


class VersionTree(object):
    """
    Holds trees of Locators to represent version histories.
    """
    def __init__(self, locator, tree_dict=None):
        """
        :param locator: must be version specific (Course has version_guid or definition had id)
        """
        assert isinstance(locator, Locator) and not inspect.isabstract(locator), \
            "locator must be a concrete subclass of Locator"
        assert locator.version(), \
            "locator must be version specific (Course has version_guid or definition had id)"
        self.locator = locator
        if tree_dict is None:
            self.children = []
        else:
            self.children = [VersionTree(child, tree_dict)
                             for child in tree_dict.get(locator.version(), [])]
