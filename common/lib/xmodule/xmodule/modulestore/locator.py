"""
Identifier for course resources.
"""

from __future__ import absolute_import
import logging
import inspect
import re
from abc import abstractmethod

from bson.objectid import ObjectId
from bson.errors import InvalidId

from opaque_keys import OpaqueKey, InvalidKeyError

from xmodule.modulestore.keys import CourseKey, UsageKey

from xmodule.modulestore.parsers import (
    parse_url,
    parse_block_ref,
    BRANCH_PREFIX,
    BLOCK_PREFIX,
    VERSION_PREFIX,
    ALLOWED_ID_RE)

log = logging.getLogger(__name__)


class LocalId(object):
    """
    Class for local ids for non-persisted xblocks (which can have hardcoded block_ids if necessary)
    """
    def __init__(self, block_id=None):
        self.block_id = block_id
        super(LocalId, self).__init__()

    def __str__(self):
        return "localid_{}".format(self.block_id or id(self))


class Locator(OpaqueKey):
    """
    A locator is like a URL, it refers to a course resource.

    Locator is an abstract base class: do not instantiate
    """

    @abstractmethod
    def url(self):
        """
        Return a string containing the URL for this location. Raises
        InvalidKeyError if the instance doesn't have a
        complete enough specification to generate a url
        """
        raise InvalidKeyError()

    def __str__(self):
        '''
        str(self) returns something like this: "mit.eecs.6002x"
        '''
        return unicode(self).encode('utf-8')

    @abstractmethod
    def version(self):
        """
        Returns the ObjectId referencing this specific location.
        Raises InvalidKeyError if the instance
        doesn't have a complete enough specification.
        """
        raise InvalidKeyError()

    @classmethod
    def as_object_id(cls, value):
        """
        Attempts to cast value as a bson.objectid.ObjectId.
        If cast fails, raises ValueError
        """
        try:
            return ObjectId(value)
        except InvalidId:
            raise ValueError('"%s" is not a valid version_guid' % value)


class BlockLocatorBase(Locator):

    # Token separating org from offering
    ORG_SEPARATOR = '+'

    def version(self):
        """
        Returns the ObjectId referencing this specific location.
        """
        return self.version_guid

    def url(self):
        """
        Return a string containing the URL for this location.
        """
        return self.NAMESPACE_SEPARATOR.join([self.CANONICAL_NAMESPACE, self._to_string()])

    @classmethod
    def _parse_url(cls, url):
        """
        url must be a string beginning with 'edx:' and containing
        either a valid version_guid or org & offering (with optional branch), or both.
        """
        if not isinstance(url, basestring):
            raise TypeError('%s is not an instance of basestring' % url)

        parse = parse_url(url)
        if not parse:
            raise InvalidKeyError(cls, url)

        if parse['version_guid']:
            parse['version_guid'] = cls.as_object_id(parse['version_guid'])

        return parse

    @property
    def package_id(self):
        if self.org and self.offering:
            return u'{}{}{}'.format(self.org, self.ORG_SEPARATOR, self.offering)
        else:
            return None


class CourseLocator(BlockLocatorBase, CourseKey):
    """
    Examples of valid CourseLocator specifications:
     CourseLocator(version_guid=ObjectId('519665f6223ebd6980884f2b'))
     CourseLocator(org='mit.eecs', offering='6.002x')
     CourseLocator(org='mit.eecs', offering='6002x', branch = 'published')
     CourseLocator.from_string('edx:version/519665f6223ebd6980884f2b')
     CourseLocator.from_string('version/519665f6223ebd6980884f2b')
     CourseLocator.from_string('edx:mit.eecs+6002x')
     CourseLocator.from_string('mit.eecs+6002x')
     CourseLocator.from_string('edx:mit.eecs+6002x/branch/published')
     CourseLocator.from_string('edx:mit.eecs+6002x/branch/published/version/519665f6223ebd6980884f2b')
     CourseLocator.from_string('mit.eecs+6002x/branch/published/version/519665f6223ebd6980884f2b')

    Should have at least a specific org & offering (id for the course as if it were a project w/
    versions) with optional 'branch',
    or version_guid (which points to a specific version). Can contain both in which case
    the persistence layer may raise exceptions if the given version != the current such version
    of the course.
    """
    CANONICAL_NAMESPACE = 'course-locator'
    KEY_FIELDS = ('org', 'offering', 'branch', 'version_guid')

    # stubs to fake out the abstractproperty class instrospection and allow treatment as attrs in instances
    org = None
    offering = None

    def __init__(self, org=None, offering=None, branch=None, version_guid=None):
        """
        Construct a CourseLocator

        Args:
            version_guid (string or ObjectId): optional unique id for the version
            org, offering (string): the standard definition. Optional only if version_guid given
            branch (string): the branch such as 'draft', 'published', 'staged', 'beta'
        """
        if version_guid:
            version_guid = self.as_object_id(version_guid)

        if not all(field is None or ALLOWED_ID_RE.match(field) for field in [org, offering, branch]):
            raise InvalidKeyError(self.__class__, [org, offering, branch])

        super(CourseLocator, self).__init__(
            org=org,
            offering=offering,
            branch=branch,
            version_guid=version_guid
        )

        if self.version_guid is None and self.org is None and self.offering is None:
            raise InvalidKeyError(self.__class__, "Either version_guid or org and offering should be set")

    @classmethod
    def _from_string(cls, serialized):
        """
        Return a CourseLocator parsing the given serialized string
        :param serialized: matches the string to
        """
        kwargs = cls._parse_url(serialized)
        try:
            return cls(**{key: kwargs.get(key) for key in cls.KEY_FIELDS})
        except ValueError:
            raise InvalidKeyError(cls, "Either version_guid or org and offering should be set: {}".format(serialized))

    def is_fully_specified(self):
        """
        Returns True if either version_guid is specified, or org+offering+branch
        are specified.
        This should always return True, since this should be validated in the constructor.
        """
        return (
            self.version_guid is not None or
            (self.org is not None and self.offering is not None and self.branch is not None)
        )

    def html_id(self):
        """
        Generate a discussion group id based on course

        To make compatible with old Location object functionality. I don't believe this behavior fits at this
        place, but I have no way to override. We should clearly define the purpose and restrictions of this
        (e.g., I'm assuming periods are fine).
        """
        return self.package_id

    def make_usage_key(self, block_type, block_id):
        return BlockUsageLocator(
            course_key=self,
            block_id=block_id
        )

    def make_asset_key(self, asset_type, path):
        raise NotImplementedError()

    def version_agnostic(self):
        """
        We don't care if the locator's version is not the current head; so, avoid version conflict
        by reducing info.
        Returns a copy of itself without any version info.

        :raises: ValueError if the block locator has no org & offering
        """
        return CourseLocator(
            org=self.org,
            offering=self.offering,
            branch=self.branch,
            version_guid=None
        )

    def course_agnostic(self):
        """
        We only care about the locator's version not its course.
        Returns a copy of itself without any course info.

        :raises: ValueError if the block locator has no version_guid
        """
        return CourseLocator(
            org=None,
            offering=None,
            branch=None,
            version_guid=self.version_guid
        )

    def for_branch(self, branch):
        """
        Return a new CourseLocator for another branch of the same course (also version agnostic)
        """
        if self.org is None:
            raise InvalidKeyError(self.__class__, "Branches must have full course ids not just versions")
        return CourseLocator(
            org=self.org,
            offering=self.offering,
            branch=branch,
            version_guid=None
        )

    def for_version(self, version_guid):
        """
        Return a new CourseLocator for another version of the same course and branch. Usually used
        when the head is updated (and thus the course x branch now points to this version)
        """
        return CourseLocator(
            org=self.org,
            offering=self.offering,
            branch=self.branch,
            version_guid=version_guid
        )

    def _to_string(self):
        """
        Return a string representing this location.
        """
        parts = []
        if self.offering:
            parts.append(unicode(self.package_id))
            if self.branch:
                parts.append(u"{prefix}{branch}".format(prefix=BRANCH_PREFIX, branch=self.branch))
        if self.version_guid:
            parts.append(u"{prefix}{guid}".format(prefix=VERSION_PREFIX, guid=self.version_guid))
        return u"/".join(parts)


class BlockUsageLocator(BlockLocatorBase, UsageKey):  # TODO implement UsageKey methods
    """
    Encodes a location.

    Locations address modules (aka blocks) which are definitions situated in a
    course instance. Thus, a Location must identify the course and the occurrence of
    the defined element in the course. Courses can be a version of an offering, the
    current draft head, or the current production version.

    Locators can contain both a version and a org + offering w/ branch. The split mongo functions
    may raise errors if these conflict w/ the current db state (i.e., the course's branch !=
    the version_guid)

    Locations can express as urls as well as dictionaries. They consist of
        package_identifier: course_guid | version_guid
        block : guid
        branch : string
    """
    CANONICAL_NAMESPACE = 'edx'
    KEY_FIELDS = ('course_key', 'block_id')

    # fake out class instrospection as this is an attr in this class's instances
    course_key = None

    def __init__(self, course_key, block_id):
        """
        Construct a BlockUsageLocator
        """
        block_id = self._parse_block_ref(block_id)
        if block_id is None:
            raise InvalidKeyError(self.__class__, "Missing block id")

        super(BlockUsageLocator, self).__init__(course_key=course_key, block_id=block_id)

    @classmethod
    def _from_string(cls, serialized):
        """
        Requests CourseLocator to deserialize its part and then adds the local deserialization of block
        """
        course_key = CourseLocator._from_string(serialized)
        parsed_parts = parse_url(serialized)
        block_id = parsed_parts.get('block_id')
        if block_id is None:
            raise InvalidKeyError(cls, serialized)
        return cls(course_key, block_id)

    def version_agnostic(self):
        """
        We don't care if the locator's version is not the current head; so, avoid version conflict
        by reducing info.
        Returns a copy of itself without any version info.

        :raises: ValueError if the block locator has no org and offering
        """
        return BlockUsageLocator(
            course_key=self.course_key.version_agnostic(),
            block_id=self.block_id
        )

    def course_agnostic(self):
        """
        We only care about the locator's version not its course.
        Returns a copy of itself without any course info.

        :raises: ValueError if the block locator has no version_guid
        """
        return BlockUsageLocator(
            course_key=self.course_key.course_agnostic(),
            block_id=self.block_id
        )

    def for_branch(self, branch):
        """
        Return a UsageLocator for the same block in a different branch of the course.
        """
        return BlockUsageLocator(
            self.course_key.for_branch(branch),
            block_id=self.block_id
        )

    @classmethod
    def _parse_block_ref(cls, block_ref):
        if isinstance(block_ref, LocalId):
            return block_ref
        else:
            parse = parse_block_ref(block_ref)
            if not parse:
                raise InvalidKeyError(cls, block_ref)
            return parse.get('block_id')

    @property
    def definition_key(self):
        raise NotImplementedError()

    @property
    def org(self):
        return self.course_key.org

    @property
    def offering(self):
        return self.course_key.offering

    @property
    def package_id(self):
        return self.course_key.package_id

    @property
    def branch(self):
        return self.course_key.branch

    @property
    def version_guid(self):
        return self.course_key.version_guid

    def is_fully_specified(self):
        return self.course_key.is_fully_specified()

    @classmethod
    def make_relative(cls, course_locator, block_id):
        """
        Return a new instance which has the given block_id in the given course
        :param course_locator: may be a BlockUsageLocator in the same snapshot
        """
        if hasattr(course_locator, 'course_key'):
            course_locator = course_locator.course_key
        return BlockUsageLocator(
            course_key=course_locator,
            block_id=block_id
        )

    def map_into_course(self, course_key):
        """
        Return a new instance which has the this block_id in the given course
        :param course_locator:
        """
        return BlockUsageLocator.make_relative(course_key, self.block_id)

    def url_reverse(self, prefix, postfix=''):
        """
        Do what reverse is supposed to do but seems unable to do. Generate a url using prefix unicode(self) postfix
        :param prefix: the beginning of the url (will be forced to begin and end with / if non-empty)
        :param postfix: the part to append to the url (will be forced to begin w/ / if non-empty)
        """
        if prefix:
            if not prefix.endswith('/'):
                prefix += '/'
            if not prefix.startswith('/'):
                prefix = '/' + prefix
        else:
            prefix = '/'
        if postfix and not postfix.startswith('/'):
            postfix = '/' + postfix
        elif postfix is None:
            postfix = ''
        return prefix + unicode(self) + postfix

    def _to_string(self):
        """
        Return a string representing this location.
        """
        return u"{course_key}/{BLOCK_PREFIX}{block_id}".format(
            course_key=self.course_key._to_string(),
            BLOCK_PREFIX=BLOCK_PREFIX,
            block_id=self.block_id
        )

    def html_id(self):
        """
        Generate a discussion group id based on course

        To make compatible with old Location object functionality. I don't believe this behavior fits at this
        place, but I have no way to override. We should clearly define the purpose and restrictions of this
        (e.g., I'm assuming periods are fine).
        """
        return re.sub('[^\w-]', '-', self._to_string())


class DefinitionLocator(Locator):
    """
    Container for how to locate a description (the course-independent content).
    """
    CANONICAL_NAMESPACE = 'defx'
    KEY_FIELDS = ('definition_id',)

    URL_RE = re.compile(r'^defx:' + VERSION_PREFIX + '([^/]+)$', re.IGNORECASE)

    def __init__(self, definition_id):
        if isinstance(definition_id, LocalId):
            super(DefinitionLocator, self).__init__(definition_id)
        elif isinstance(definition_id, basestring):
            regex_match = self.URL_RE.match(definition_id)
            if regex_match is not None:
                super(DefinitionLocator, self).__init__(self.as_object_id(regex_match.group(1)))
            else:
                super(DefinitionLocator, self).__init__(self.as_object_id(definition_id))
        else:
            super(DefinitionLocator, self).__init__(self.as_object_id(definition_id))

    def _to_string(self):
        '''
        Return a string representing this location.
        unicode(self) returns something like this: "version/519665f6223ebd6980884f2b"
        '''
        return VERSION_PREFIX + str(self.definition_id)

    def url(self):
        """
        Return a string containing the URL for this location.
        url(self) returns something like this: 'defx:version/519665f6223ebd6980884f2b'
        """
        return u'defx:' + self._to_string()

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
        if not isinstance(locator, Locator) and not inspect.isabstract(locator):
            raise TypeError("locator {} must be a concrete subclass of Locator".format(locator))
        if not locator.version():
            raise ValueError("locator must be version specific (Course has version_guid or definition had id)")
        self.locator = locator
        if tree_dict is None:
            self.children = []
        else:
            self.children = [VersionTree(child, tree_dict)
                             for child in tree_dict.get(locator.version(), [])]
