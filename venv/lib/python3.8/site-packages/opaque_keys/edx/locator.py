"""
Identifier for course resources.
"""

import inspect
import logging
import re
import warnings
from uuid import UUID

from bson.errors import InvalidId
from bson.objectid import ObjectId
from bson.son import SON

from opaque_keys import OpaqueKey, InvalidKeyError
from opaque_keys.edx.keys import AssetKey, CourseKey, DefinitionKey, LearningContextKey, UsageKey, UsageKeyV2

log = logging.getLogger(__name__)


class LocalId:
    """
    Class for local ids for non-persisted xblocks (which can have hardcoded block_ids if necessary)
    """
    def __init__(self, block_id=None):
        self.block_id = block_id
        super().__init__()

    def __str__(self):
        identifier = self.block_id or id(self)
        return f"localid_{identifier}"


class Locator(OpaqueKey):
    """
    A locator identifies a course resource.

    Locator is an abstract base class: do not instantiate
    """

    BLOCK_TYPE_PREFIX = r"type"
    # Prefix for the version portion of a locator URL, when it is preceded by a course ID
    VERSION_PREFIX = r"version"
    ALLOWED_ID_CHARS = r'[\w\-~.:]'
    DEPRECATED_ALLOWED_ID_CHARS = r'[\w\-~.:%]'

    @property
    def version(self):  # pragma: no cover
        """
        Returns the ObjectId referencing this specific location.

        Raises:
            InvalidKeyError: if the instance doesn't have a complete enough specification.
        """
        raise NotImplementedError()

    @classmethod
    def as_object_id(cls, value):
        """
        Attempts to cast value as a bson.objectid.ObjectId.

        Raises:
            ValueError: if casting fails
        """
        try:
            return ObjectId(value)
        except InvalidId as key_error:
            raise InvalidKeyError(cls, f'"{value}" is not a valid version_guid') from key_error


class CheckFieldMixin:
    """
    Mixin that provides handy methods for checking field types/values.
    """
    @classmethod
    def _check_key_string_field(cls, field_name, value, regexp=re.compile(r'^[a-zA-Z0-9_\-.]+$')):
        """
        Helper method to verify that a key's string field(s) meet certain
        requirements:
            Are a non-empty string
            Match the specified regular expression
        """
        if not isinstance(value, str):
            raise TypeError(f"Expected a string, got {field_name}={value!r}")
        if not value or not re.match(regexp, value):
            raise ValueError(
                f"{value!r} is not a valid {cls.__name__}.{field_name} field value."
            )


# `BlockLocatorBase` is another abstract base class, so don't worry that it doesn't
# provide implementations for _from_string, _to_string, and version.
# pylint: disable=abstract-method
class BlockLocatorBase(Locator):
    """
    Abstract base clase for XBlock locators.

    See subclasses for more detail, particularly `CourseLocator` and `BlockUsageLocator`.
    """
    # Prefix for the branch portion of a locator URL
    BRANCH_PREFIX = r"branch"
    # Prefix for the block portion of a locator URL
    BLOCK_PREFIX = r"block"
    BLOCK_ALLOWED_ID_CHARS = r'[\w\-~.:%]'

    ALLOWED_ID_RE = re.compile(r'^' + Locator.ALLOWED_ID_CHARS + r'+\Z', re.UNICODE)
    DEPRECATED_ALLOWED_ID_RE = re.compile(r'^' + Locator.DEPRECATED_ALLOWED_ID_CHARS + r'+\Z', re.UNICODE)

    URL_RE_SOURCE = """
        ((?P<org>{ALLOWED_ID_CHARS}+)\\+(?P<course>{ALLOWED_ID_CHARS}+)(\\+(?P<run>{ALLOWED_ID_CHARS}+))?{SEP})??
        ({BRANCH_PREFIX}@(?P<branch>{ALLOWED_ID_CHARS}+){SEP})?
        ({VERSION_PREFIX}@(?P<version_guid>[a-f0-9]+){SEP})?
        ({BLOCK_TYPE_PREFIX}@(?P<block_type>{ALLOWED_ID_CHARS}+){SEP})?
        ({BLOCK_PREFIX}@(?P<block_id>{BLOCK_ALLOWED_ID_CHARS}+))?
    """.format(
        ALLOWED_ID_CHARS=Locator.ALLOWED_ID_CHARS,
        BLOCK_ALLOWED_ID_CHARS=BLOCK_ALLOWED_ID_CHARS,
        BRANCH_PREFIX=BRANCH_PREFIX,
        VERSION_PREFIX=Locator.VERSION_PREFIX,
        BLOCK_TYPE_PREFIX=Locator.BLOCK_TYPE_PREFIX,
        BLOCK_PREFIX=BLOCK_PREFIX,
        SEP=r'(\+(?=.)|\Z)',  # Separator: requires a non-trailing '+' or end of string
    )

    URL_RE = re.compile('^' + URL_RE_SOURCE + r'\Z', re.VERBOSE | re.UNICODE)

    @classmethod
    def parse_url(cls, string):  # pylint: disable=redefined-outer-name
        """
        If it can be parsed as a version_guid with no preceding org + offering, returns a dict
        with key 'version_guid' and the value,

        If it can be parsed as a org + offering, returns a dict
        with key 'id' and optional keys 'branch' and 'version_guid'.

        Raises:
            InvalidKeyError: if string cannot be parsed -or- string ends with a newline.
        """
        match = cls.URL_RE.match(string)
        if not match:
            raise InvalidKeyError(cls, string)
        return match.groupdict()


class CourseLocator(BlockLocatorBase, CourseKey):   # pylint: disable=abstract-method
    """
    Examples of valid CourseLocator specifications:
     CourseLocator(version_guid=ObjectId('519665f6223ebd6980884f2b'))
     CourseLocator(org='mit.eecs', course='6.002x', run='T2_2014')
     CourseLocator(org='mit.eecs', course='6002x', run='fall_2014' branch = 'published')
     CourseLocator.from_string('course-v1:version@519665f6223ebd6980884f2b')
     CourseLocator.from_string('course-v1:mit.eecs+6002x')
     CourseLocator.from_string('course-v1:mit.eecs+6002x+branch@published')
     CourseLocator.from_string('course-v1:mit.eecs+6002x+branch@published+version@519665f6223ebd6980884f2b')

    Should have at least a specific org, course, and run with optional 'branch',
    or version_guid (which points to a specific version). Can contain both in which case
    the persistence layer may raise exceptions if the given version != the current such version
    of the course.
    """

    # pylint: disable=no-member

    CANONICAL_NAMESPACE = 'course-v1'
    KEY_FIELDS = ('org', 'course', 'run', 'branch', 'version_guid')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    # Characters that are forbidden in the deprecated format
    INVALID_CHARS_DEPRECATED = re.compile(r"[^\w.%-]", re.UNICODE)

    def __init__(self, org=None, course=None, run=None, branch=None, version_guid=None, deprecated=False, **kwargs):
        """
        Construct a CourseLocator

        Args:
            version_guid (string or ObjectId): optional unique id for the version
            org, course, run (string): the standard definition. Optional only if version_guid given
            branch (string): the branch such as 'draft', 'published', 'staged', 'beta'
        """
        offering_arg = kwargs.pop('offering', None)
        if offering_arg:
            warnings.warn(
                "offering is deprecated! Use course and run instead.",
                DeprecationWarning,
                stacklevel=2
            )
            course, __, run = offering_arg.partition("/")

        if deprecated:
            for part in (org, course, run):
                self._check_location_part(part, self.INVALID_CHARS_DEPRECATED)

            fields = [org, course]
            # Deprecated style allowed to have None for run and branch, and allowed to have '' for run
            if run:
                fields.append(run)
            if branch is not None:
                fields.append(branch)
            if not all(self.DEPRECATED_ALLOWED_ID_RE.match(field) for field in fields):
                raise InvalidKeyError(self.__class__, fields)

        else:
            if version_guid:
                version_guid = self.as_object_id(version_guid)

            for name, value in [['org', org], ['course', course], ['run', run], ['branch', branch]]:
                if not (value is None or self.ALLOWED_ID_RE.match(value)):
                    raise InvalidKeyError(self.__class__,
                                          f"Special characters not allowed in field {name}: '{value}'")

        super().__init__(
            org=org,
            course=course,
            run=run,
            branch=branch,
            version_guid=version_guid,
            deprecated=deprecated,
            **kwargs
        )

        if self.deprecated and (self.org is None or self.course is None):
            raise InvalidKeyError(self.__class__, "Deprecated strings must set both org and course.")

        if not self.deprecated and self.version_guid is None and \
                (self.org is None or self.course is None or self.run is None):
            raise InvalidKeyError(self.__class__, "Either version_guid or org, course, and run should be set")

    @classmethod
    def _check_location_part(cls, val, regexp):  # pylint: disable=missing-docstring
        if val is None:
            return
        if not isinstance(val, str):
            raise InvalidKeyError(cls, f"{val!r} is not a string")
        if regexp.search(val) is not None:
            raise InvalidKeyError(cls, f"Invalid characters in {val!r}.")

    @property
    def version(self):
        """
        Deprecated. The ambiguously named field from CourseLocation which code
        expects to find. Equivalent to version_guid.
        """
        warnings.warn(
            "version is no longer supported as a property of Locators. Please use the version_guid property.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.version_guid

    @property
    def offering(self):
        """
        Deprecated. Use course and run independently.
        """
        warnings.warn(
            "Offering is no longer a supported property of Locator. Please use the course and run properties.",
            DeprecationWarning,
            stacklevel=2
        )

        if not self.course and not self.run:
            return None
        if not self.run and self.course:
            return self.course
        return "/".join([self.course, self.run])

    @classmethod
    def _from_string(cls, serialized):
        """
        Return a CourseLocator parsing the given serialized string
        :param serialized: matches the string to a CourseLocator
        """
        parse = cls.parse_url(serialized)

        if parse['version_guid']:
            parse['version_guid'] = cls.as_object_id(parse['version_guid'])

        return cls(**{key: parse.get(key) for key in cls.KEY_FIELDS})

    def html_id(self):
        """
        Return an id which can be used on an html page as an id attr of an html element.

        To make compatible with old Location object functionality. I don't believe this behavior fits at this
        place, but I have no way to override. We should clearly define the purpose and restrictions of this
        (e.g., I'm assuming periods are fine).
        """
        return str(self)

    def make_usage_key(self, block_type, block_id):
        return BlockUsageLocator(
            course_key=self,
            block_type=block_type,
            block_id=block_id,
            deprecated=self.deprecated,
        )

    def make_asset_key(self, asset_type, path):
        return AssetLocator(self, asset_type, path, deprecated=self.deprecated)

    def make_usage_key_from_deprecated_string(self, location_url):
        """
        Deprecated mechanism for creating a UsageKey given a CourseKey and a serialized Location.

        NOTE: this prejudicially takes the tag, org, and course from the url not self.

        Raises:
            InvalidKeyError: if the url does not parse
        """
        warnings.warn(
            "make_usage_key_from_deprecated_string is deprecated! Please use make_usage_key",
            DeprecationWarning,
            stacklevel=2
        )
        return BlockUsageLocator.from_string(location_url).replace(run=self.run)

    def version_agnostic(self):
        """
        We don't care if the locator's version is not the current head; so, avoid version conflict
        by reducing info.
        Returns a copy of itself without any version info.

        Raises:
            ValueError: if the block locator has no org & course, run
        """
        return self.replace(version_guid=None)

    def course_agnostic(self):
        """
        We only care about the locator's version not its course.
        Returns a copy of itself without any course info.

        Raises:
            ValueError: if the block locator has no version_guid
        """
        return self.replace(org=None, course=None, run=None, branch=None)

    def for_branch(self, branch):
        """
        Return a new CourseLocator for another branch of the same course (also version agnostic)
        """
        if self.org is None:
            raise InvalidKeyError(self.__class__, "Branches must have full course ids not just versions")
        return self.replace(branch=branch, version_guid=None)

    def for_version(self, version_guid):
        """
        Return a new CourseLocator for another version of the same course and branch. Usually used
        when the head is updated (and thus the course x branch now points to this version)
        """
        return self.replace(version_guid=version_guid)

    def _to_string(self):
        """
        Return a string representing this location.
        """
        parts = []
        if self.course and self.run:
            parts.extend([self.org, self.course, self.run])
            if self.branch:
                parts.append(f"{self.BRANCH_PREFIX}@{self.branch}")
        if self.version_guid:
            parts.append(f"{self.VERSION_PREFIX}@{self.version_guid}")
        return "+".join(parts)

    def _to_deprecated_string(self):
        """Returns an 'old-style' course id, represented as 'org/course/run'"""
        return '/'.join([self.org, self.course, self.run])

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """
        Return an instance of `cls` parsed from its deprecated `serialized` form.

        This will be called only if :meth:`OpaqueKey.from_string` is unable to
        parse a key out of `serialized`, and only if `set_deprecated_fallback` has
        been called to register a fallback class.

        Args:
            cls: The :class:`OpaqueKey` subclass.
            serialized (unicode): A serialized :class:`OpaqueKey`, with namespace already removed.

        Raises:
            InvalidKeyError: Should be raised if `serialized` is not a valid serialized key
                understood by `cls`.
        """
        if serialized.count('/') != 2:
            raise InvalidKeyError(cls, serialized)

        return cls(*serialized.split('/'), deprecated=True)


CourseKey.set_deprecated_fallback(CourseLocator)
LearningContextKey.set_deprecated_fallback(CourseLocator)


class LibraryLocator(BlockLocatorBase, CourseKey):
    """
    Locates a library. Libraries are XBlock structures with a 'library' block
    at their root.

    Libraries are treated analogously to courses for now. Once opaque keys are
    better supported, they will no longer have the 'run' property, and may no
    longer conform to CourseKey but rather some more general key type.

    Examples of valid LibraryLocator specifications:
     LibraryLocator(version_guid=ObjectId('519665f6223ebd6980884f2b'))
     LibraryLocator(org='UniX', library='PhysicsProbs')
     LibraryLocator.from_string('library-v1:UniX+PhysicsProbs')

    version_guid is optional.

    The constructor accepts 'course' as a deprecated alias for the 'library'
    attribute.

    branch is optional.
    """
    CANONICAL_NAMESPACE = 'library-v1'
    RUN = 'library'  # For backwards compatibility, LibraryLocators have a read-only 'run' property equal to this
    KEY_FIELDS = ('org', 'library', 'branch', 'version_guid')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False
    is_course = False  # These keys inherit from CourseKey for historical reasons but are not courses

    def __init__(self, org=None, library=None, branch=None, version_guid=None, **kwargs):
        """
        Construct a LibraryLocator

        Args:
            version_guid (string or ObjectId): optional unique id for the version
            org, library: the standard definition. Optional only if version_guid given.
            branch (string): the optional branch such as 'draft', 'published', 'staged', 'beta'
        """
        if 'offering' in kwargs:
            raise ValueError("'offering' is not a valid field for a LibraryLocator.")

        if 'course' in kwargs:
            if library is not None:
                raise ValueError("Cannot specify both 'library' and 'course'")
            warnings.warn(
                "For LibraryLocators, use 'library' instead of 'course'.",
                DeprecationWarning,
                stacklevel=2
            )
            library = kwargs.pop('course')

        run = kwargs.pop('run', self.RUN)
        if run != self.RUN:
            raise ValueError(f"Invalid run. Should be '{self.RUN}' or None.")

        if version_guid:
            version_guid = self.as_object_id(version_guid)

        for name, value in [['org', org], ['library', library], ['branch', branch]]:
            if not (value is None or self.ALLOWED_ID_RE.match(value)):
                raise InvalidKeyError(self.__class__,
                                      f"Special characters not allowed in field {name}: '{value}'")

        if kwargs.get('deprecated', False):
            raise InvalidKeyError(self.__class__, 'LibraryLocator cannot have deprecated=True')

        super().__init__(
            org=org,
            library=library,
            branch=branch,
            version_guid=version_guid,
            **kwargs
        )

        if self.version_guid is None and (self.org is None or self.library is None):  # pylint: disable=no-member
            raise InvalidKeyError(self.__class__, "Either version_guid or org and library should be set")

    @property
    def run(self):
        """
        Deprecated. Return a 'run' for compatibility with CourseLocator.
        """
        warnings.warn("Accessing 'run' on a LibraryLocator is deprecated.", DeprecationWarning, stacklevel=2)
        return self.RUN

    @property
    def course(self):
        """
        Deprecated. Return a 'course' for compatibility with CourseLocator.
        """
        warnings.warn("Accessing 'course' on a LibraryLocator is deprecated.", DeprecationWarning, stacklevel=2)
        return self.library  # pylint: disable=no-member

    @property
    def version(self):
        """
        Deprecated. The ambiguously named field from CourseLocation which code
        expects to find. Equivalent to version_guid.
        """
        warnings.warn(
            "version is no longer supported as a property of Locators. Please use the version_guid property.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.version_guid  # pylint: disable=no-member

    @classmethod
    def _from_string(cls, serialized):
        """
        Return a LibraryLocator parsing the given serialized string
        :param serialized: matches the string to a LibraryLocator
        """
        parse = cls.parse_url(serialized)

        # The regex detects the "library" key part as "course"
        # since we're sharing a regex with CourseLocator
        parse["library"] = parse["course"]
        del parse["course"]

        if parse['version_guid']:
            parse['version_guid'] = cls.as_object_id(parse['version_guid'])

        return cls(**{key: parse.get(key) for key in cls.KEY_FIELDS})

    def html_id(self):
        """
        Return an id which can be used on an html page as an id attr of an html element.
        """
        return str(self)

    def make_usage_key(self, block_type, block_id):
        return LibraryUsageLocator(
            library_key=self,
            block_type=block_type,
            block_id=block_id,
        )

    def make_asset_key(self, asset_type, path):
        return AssetLocator(self, asset_type, path, deprecated=False)

    def version_agnostic(self):
        """
        We don't care if the locator's version is not the current head; so, avoid version conflict
        by reducing info.
        Returns a copy of itself without any version info.

        Raises:
            ValueError: if the block locator has no org & course, run
        """
        return self.replace(version_guid=None)

    def course_agnostic(self):
        """
        We only care about the locator's version not its library.
        Returns a copy of itself without any library info.

        Raises:
            ValueError: if the block locator has no version_guid
        """
        return self.replace(org=None, library=None, branch=None)

    def for_branch(self, branch):
        """
        Return a new CourseLocator for another branch of the same library (also version agnostic)
        """
        if self.org is None and branch is not None:
            raise InvalidKeyError(self.__class__, "Branches must have full library ids not just versions")
        return self.replace(branch=branch, version_guid=None)

    def for_version(self, version_guid):
        """
        Return a new LibraryLocator for another version of the same library and branch. Usually used
        when the head is updated (and thus the library x branch now points to this version)
        """
        return self.replace(version_guid=version_guid)

    def _to_string(self):
        """
        Return a string representing this location.
        """
        parts = []
        if self.library:  # pylint: disable=no-member
            parts.extend([self.org, self.library])  # pylint: disable=no-member
            if self.branch:  # pylint: disable=no-member
                parts.append(f"{self.BRANCH_PREFIX}@{self.branch}")  # pylint: disable=no-member
        if self.version_guid:  # pylint: disable=no-member
            parts.append(f"{self.VERSION_PREFIX}@{self.version_guid}")  # pylint: disable=no-member
        return "+".join(parts)

    def _to_deprecated_string(self):
        """ LibraryLocators are never deprecated. """
        raise NotImplementedError

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """ LibraryLocators are never deprecated. """
        raise NotImplementedError


class BlockUsageLocator(BlockLocatorBase, UsageKey):
    """
    Encodes a location.

    Locations address modules (aka blocks) which are definitions situated in a
    course instance. Thus, a Location must identify the course and the occurrence of
    the defined element in the course. Courses can be a version of an offering, the
    current draft head, or the current production version.

    Locators can contain both a version and a org + course + run w/ branch. The split mongo functions
    may raise errors if these conflict w/ the current db state (i.e., the course's branch !=
    the version_guid)

    Locations can express as urls as well as dictionaries. They consist of
        package_identifier: course_guid | version_guid
        block : guid
        branch : string

    BlockUsageLocators also support deprecated Location-style formatting with the following mapping:
    Location(org, course, run, category, name, revision) is represented as a BlockUsageLocator with:

      - course_key = a CourseKey comprised of (org, course, run, branch=revision)

      - block_type = category

      - block_id = name
    """
    CANONICAL_NAMESPACE = 'block-v1'
    KEY_FIELDS = ('course_key', 'block_type', 'block_id')
    CHECKED_INIT = False

    DEPRECATED_TAG = 'i4x'  # to combine Locations with BlockUsageLocators

    # fake out class introspection as this is an attr in this class's instances
    course_key = None
    block_type = None

    DEPRECATED_URL_RE = re.compile("""
        i4x://
        (?P<org>[^/]+)/
        (?P<course>[^/]+)/
        (?P<category>[^/]+)/     # category == block_type
        (?P<name>[^@]+)          # name == block_id
        (@(?P<revision>[^/]+))?  # branch == revision
        \\Z
    """, re.VERBOSE)

    # TODO (cpennington): We should decide whether we want to expand the
    # list of valid characters in a location
    DEPRECATED_INVALID_CHARS = re.compile(r"[^\w.%-]", re.UNICODE)
    # Names are allowed to have colons.
    DEPRECATED_INVALID_CHARS_NAME = re.compile(r"[^\w.:%-]", re.UNICODE)

    # html ids can contain word chars and dashes
    DEPRECATED_INVALID_HTML_CHARS = re.compile(r"[^\w-]", re.UNICODE)

    def __init__(self, course_key, block_type, block_id, **kwargs):
        """
        Construct a BlockUsageLocator
        """
        # Always use the deprecated status of the course key
        deprecated = kwargs['deprecated'] = course_key.deprecated
        block_id = self._parse_block_ref(block_id, deprecated)
        if block_id is None and not deprecated:
            raise InvalidKeyError(self.__class__, "Missing block id")

        super().__init__(course_key=course_key, block_type=block_type, block_id=block_id, **kwargs)

    def replace(self, **kwargs):
        # BlockUsageLocator allows for the replacement of 'KEY_FIELDS' in 'self.course_key'.
        # This includes the deprecated 'KEY_FIELDS' of CourseLocator `'revision'` and `'version'`.
        course_key_kwargs = {}
        for key in CourseLocator.KEY_FIELDS:
            if key in kwargs:
                course_key_kwargs[key] = kwargs.pop(key)
        if 'revision' in kwargs and 'branch' not in course_key_kwargs:
            course_key_kwargs['branch'] = kwargs.pop('revision')
        if 'version' in kwargs and 'version_guid' not in course_key_kwargs:
            course_key_kwargs['version_guid'] = kwargs.pop('version')
        if course_key_kwargs:
            kwargs['course_key'] = self.course_key.replace(**course_key_kwargs)

        # `'name'` and `'category'` are deprecated `KEY_FIELDS`.
        # Their values are reassigned to the new keys.
        if 'name' in kwargs and 'block_id' not in kwargs:
            kwargs['block_id'] = kwargs.pop('name')
        if 'category' in kwargs and 'block_type' not in kwargs:
            kwargs['block_type'] = kwargs.pop('category')
        return super().replace(**kwargs)

    @classmethod
    def _clean(cls, value, invalid):
        """
        Should only be called on deprecated-style values

        invalid should be a compiled regexp of chars to replace with '_'
        """
        return re.sub('_+', '_', invalid.sub('_', value))

    @classmethod
    def clean(cls, value):
        """
        Should only be called on deprecated-style values

        Return value, made into a form legal for locations
        """
        return cls._clean(value, cls.DEPRECATED_INVALID_CHARS)

    @classmethod
    def clean_keeping_underscores(cls, value):
        """
        Should only be called on deprecated-style values

        Return value, replacing INVALID_CHARS, but not collapsing multiple '_' chars.
        This for cleaning asset names, as the YouTube ID's may have underscores in them, and we need the
        transcript asset name to match. In the future we may want to change the behavior of _clean.
        """
        return cls.DEPRECATED_INVALID_CHARS.sub('_', value)

    @classmethod
    def clean_for_url_name(cls, value):
        """
        Should only be called on deprecated-style values

        Convert value into a format valid for location names (allows colons).
        """
        return cls._clean(value, cls.DEPRECATED_INVALID_CHARS_NAME)

    @classmethod
    def clean_for_html(cls, value):
        """
        Should only be called on deprecated-style values

        Convert a string into a form that's safe for use in html ids, classes, urls, etc.
        Replaces all INVALID_HTML_CHARS with '_', collapses multiple '_' chars
        """
        return cls._clean(value, cls.DEPRECATED_INVALID_HTML_CHARS)

    @classmethod
    def _from_string(cls, serialized):
        """
        Requests CourseLocator to deserialize its part and then adds the local deserialization of block
        """
        # Allow access to _from_string protected method
        course_key = CourseLocator._from_string(serialized)  # pylint: disable=protected-access
        parsed_parts = cls.parse_url(serialized)
        block_id = parsed_parts.get('block_id', None)
        if block_id is None:
            raise InvalidKeyError(cls, serialized)
        return cls(course_key, parsed_parts.get('block_type'), block_id)

    def version_agnostic(self):
        """
        We don't care if the locator's version is not the current head; so, avoid version conflict
        by reducing info.
        Returns a copy of itself without any version info.

        Raises:
            ValueError: if the block locator has no org, course, and run
        """
        return self.replace(course_key=self.course_key.version_agnostic())

    def course_agnostic(self):
        """
        We only care about the locator's version not its course.
        Returns a copy of itself without any course info.

        Raises:
            ValueError if the block locator has no version_guid
        """
        return self.replace(course_key=self.course_key.course_agnostic())

    def for_branch(self, branch):
        """
        Return a UsageLocator for the same block in a different branch of the course.
        """
        return self.replace(course_key=self.course_key.for_branch(branch))

    def for_version(self, version_guid):
        """
        Return a UsageLocator for the same block in a different branch of the course.
        """
        return self.replace(course_key=self.course_key.for_version(version_guid))

    @classmethod
    def _parse_block_ref(cls, block_ref, deprecated=False):
        """
        Given `block_ref`, tries to parse it into a valid block reference.

        Returns `block_ref` if it is valid.

        Raises:
            InvalidKeyError: if `block_ref` is invalid.
        """

        if deprecated and block_ref is None:
            return None

        if isinstance(block_ref, LocalId):
            return block_ref

        is_valid_deprecated = deprecated and cls.DEPRECATED_ALLOWED_ID_RE.match(block_ref)
        is_valid = cls.ALLOWED_ID_RE.match(block_ref)

        # pylint: disable=no-else-return
        if is_valid or is_valid_deprecated:
            return block_ref
        else:
            raise InvalidKeyError(cls, block_ref)

    @property
    def definition_key(self):  # pragma: no cover
        """
        Returns the definition key for this object.
        Undefined for Locators.
        """
        raise NotImplementedError()

    @property
    def org(self):
        """Returns the org for this object's course_key."""
        return self.course_key.org

    @property
    def course(self):
        """Returns the course for this object's course_key."""
        return self.course_key.course

    @property
    def run(self):
        """Returns the run for this object's course_key."""
        return self.course_key.run

    @property
    def offering(self):
        """
        Deprecated. Use course and run independently.
        """
        warnings.warn(
            "Offering is no longer a supported property of Locator. Please use the course and run properties.",
            DeprecationWarning,
            stacklevel=2
        )

        # pylint: disable=no-else-return
        if not self.course and not self.run:
            return None
        elif not self.run and self.course:
            return self.course
        return "/".join([self.course, self.run])

    @property
    def branch(self):
        """Returns the branch for this object's course_key."""
        return self.course_key.branch

    @property
    def version_guid(self):
        """Returns the version guid for this object."""
        return self.course_key.version_guid

    @property
    def version(self):
        """
        Deprecated. The ambiguously named field from CourseLocation which code
        expects to find. Equivalent to version_guid.
        """
        warnings.warn(
            "Version is no longer supported as a property of Locators. Please use the version_guid property.",
            DeprecationWarning,
            stacklevel=2
        )

        # Returns the version guid for this object.
        return self.course_key.version_guid

    @property
    def name(self):
        """
        Deprecated. The ambiguously named field from Location which code
        expects to find. Equivalent to block_id.
        """
        warnings.warn(
            "Name is no longer supported as a property of Locators. Please use the block_id property.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.block_id

    @property
    def category(self):
        """
        Deprecated. The ambiguously named field from Location which code
        expects to find. Equivalent to block_type.
        """
        warnings.warn(
            "Category is no longer supported as a property of Locators. Please use the block_type property.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.block_type

    @property
    def revision(self):
        """
        Deprecated. The ambiguously named field from Location which code
        expects to find. Equivalent to branch.
        """
        warnings.warn(
            "Revision is no longer supported as a property of Locators. Please use the branch property.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.branch

    def is_fully_specified(self):
        """Returns boolean; whether or not this object's course_key is fully specified."""
        return self.course_key.is_fully_specified()

    @classmethod
    def make_relative(cls, course_locator, block_type, block_id):
        """
        Return a new instance which has the given block_id in the given course
        :param course_locator: may be a BlockUsageLocator in the same snapshot
        """
        if hasattr(course_locator, 'course_key'):
            course_locator = course_locator.course_key
        return course_locator.make_usage_key(
            block_type=block_type,
            block_id=block_id
        )

    def map_into_course(self, course_key):
        """
        Return a new instance which has the this block_id in the given course
        :param course_key: a CourseKey object representing the new course to map into
        """
        return self.replace(course_key=course_key)

    def _to_string(self):
        """
        Return a string representing this location.
        """
        # Allow access to _to_string protected method
        return (
            f"{self.course_key._to_string()}"  # pylint: disable=protected-access
            f"+{self.BLOCK_TYPE_PREFIX}"
            f"@{self.block_type}+{self.BLOCK_PREFIX}@{self.block_id}"
        )

    def html_id(self):
        """
        Return an id which can be used on an html page as an id attr of an html element.  It is currently also
        persisted by some clients to identify blocks.

        To make compatible with old Location object functionality. I don't believe this behavior fits at this
        place, but I have no way to override. We should clearly define the purpose and restrictions of this
        (e.g., I'm assuming periods are fine).
        """
        if self.deprecated:
            id_fields = [self.DEPRECATED_TAG, self.org, self.course, self.block_type, self.block_id, self.version_guid]
            id_string = "-".join([v for v in id_fields if v is not None])
            return self.clean_for_html(id_string)
        return self.block_id

    def _to_deprecated_string(self):
        """
        Returns an old-style location, represented as:
        i4x://org/course/category/name[@revision]  # Revision is optional
        """
        url = (
            f"{self.DEPRECATED_TAG}://{self.course_key.org}/{self.course_key.course}"
            f"/{self.block_type}/{self.block_id}"
        )
        if self.course_key.branch:
            url += f"@{self.course_key.branch}"
        return url

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """
        Return an instance of `cls` parsed from its deprecated `serialized` form.

        This will be called only if :meth:`OpaqueKey.from_string` is unable to
        parse a key out of `serialized`, and only if `set_deprecated_fallback` has
        been called to register a fallback class.

        Args:
            cls: The :class:`OpaqueKey` subclass.
            serialized (unicode): A serialized :class:`OpaqueKey`, with namespace already removed.

        Raises:
            InvalidKeyError: Should be raised if `serialized` is not a valid serialized key
                understood by `cls`.
        """
        match = cls.DEPRECATED_URL_RE.match(serialized)
        if match is None:
            raise InvalidKeyError(BlockUsageLocator, serialized)
        groups = match.groupdict()
        course_key = CourseLocator(
            org=groups['org'],
            course=groups['course'],
            run=None,
            branch=groups.get('revision'),
            deprecated=True,
        )
        return cls(course_key, groups['category'], groups['name'], deprecated=True)

    def to_deprecated_son(self, prefix='', tag='i4x'):
        """
        Returns a SON object that represents this location
        """
        # This preserves the old SON keys ('tag', 'org', 'course', 'category', 'name', 'revision'),
        # because that format was used to store data historically in mongo

        # adding tag b/c deprecated form used it
        son = SON({prefix + 'tag': tag})
        for field_name in ('org', 'course'):
            # Temporary filtering of run field because deprecated form left it out
            son[prefix + field_name] = getattr(self.course_key, field_name)
        for (dep_field_name, field_name) in [('category', 'block_type'), ('name', 'block_id')]:
            son[prefix + dep_field_name] = getattr(self, field_name)

        son[prefix + 'revision'] = self.course_key.branch
        return son

    @classmethod
    def _from_deprecated_son(cls, id_dict, run):
        """
        Return the Location decoding this id_dict and run
        """
        course_key = CourseLocator(
            id_dict['org'],
            id_dict['course'],
            run,
            id_dict['revision'],
            deprecated=True,
        )
        return cls(course_key, id_dict['category'], id_dict['name'], deprecated=True)


# register BlockUsageLocator as the deprecated fallback for UsageKey
UsageKey.set_deprecated_fallback(BlockUsageLocator)


class LibraryUsageLocator(BlockUsageLocator):
    """
    Just like BlockUsageLocator, but this points to a block stored in a library,
    not a course.
    """
    CANONICAL_NAMESPACE = 'lib-block-v1'
    KEY_FIELDS = ('library_key', 'block_type', 'block_id')

    # fake out class introspection as this is an attr in this class's instances
    library_key = None
    block_type = None

    def __init__(self, library_key, block_type, block_id, **kwargs):
        """
        Construct a LibraryUsageLocator
        """
        # LibraryUsageLocator is a new type of locator so should never be deprecated.
        if library_key.deprecated or kwargs.get('deprecated', False):
            raise InvalidKeyError(self.__class__, "LibraryUsageLocators are never deprecated.")

        block_id = self._parse_block_ref(block_id, False)

        try:
            if not all(self.ALLOWED_ID_RE.match(val) for val in (block_type, block_id)):
                raise InvalidKeyError(
                    self.__class__,
                    f"Invalid block_type or block_id ({block_type!r}, {block_id!r})"
                )
        except TypeError as error:
            raise InvalidKeyError(
                self.__class__,
                f"Invalid block_type or block_id ({block_type!r}, {block_id!r})"
            ) from error

        # We skip the BlockUsageLocator init and go to its superclass:
        # pylint: disable=bad-super-call
        super(BlockUsageLocator, self).__init__(library_key=library_key, block_type=block_type, block_id=block_id,
                                                **kwargs)

    def replace(self, **kwargs):
        # BlockUsageLocator allows for the replacement of 'KEY_FIELDS' in 'self.library_key'
        lib_key_kwargs = {}
        for key in LibraryLocator.KEY_FIELDS:
            if key in kwargs:
                lib_key_kwargs[key] = kwargs.pop(key)
        if 'version' in kwargs and 'version_guid' not in lib_key_kwargs:
            lib_key_kwargs['version_guid'] = kwargs.pop('version')
        if lib_key_kwargs:
            kwargs['library_key'] = self.library_key.replace(**lib_key_kwargs)
        if 'course_key' in kwargs:
            kwargs['library_key'] = kwargs.pop('course_key')
        return super().replace(**kwargs)

    @classmethod
    def _from_string(cls, serialized):
        """
        Requests LibraryLocator to deserialize its part and then adds the local deserialization of block
        """
        # Allow access to _from_string protected method
        library_key = LibraryLocator._from_string(serialized)  # pylint: disable=protected-access
        parsed_parts = LibraryLocator.parse_url(serialized)

        block_id = parsed_parts.get('block_id', None)
        if block_id is None:
            raise InvalidKeyError(cls, serialized)

        block_type = parsed_parts.get('block_type')
        if block_type is None:
            raise InvalidKeyError(cls, serialized)

        return cls(library_key, parsed_parts.get('block_type'), block_id)

    def version_agnostic(self):
        """
        We don't care if the locator's version is not the current head; so, avoid version conflict
        by reducing info.
        Returns a copy of itself without any version info.

        Raises:
            ValueError: if the block locator has no org, course, and run
        """
        return self.replace(library_key=self.library_key.version_agnostic())

    def for_branch(self, branch):
        """
        Return a UsageLocator for the same block in a different branch of the library.
        """
        return self.replace(library_key=self.library_key.for_branch(branch))

    def for_version(self, version_guid):
        """
        Return a UsageLocator for the same block in a different version of the library.
        """
        return self.replace(library_key=self.library_key.for_version(version_guid))

    @property
    def course_key(self):
        """
        To enable compatibility with BlockUsageLocator, we provide a read-only
        course_key property.
        """
        return self.library_key

    @property
    def run(self):
        """Returns the run for this object's library_key."""
        warnings.warn(
            "Run is a deprecated property of LibraryUsageLocators.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.library_key.RUN

    def _to_deprecated_string(self):
        """ Disable some deprecated methods of our parent class. """
        raise NotImplementedError

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """ Disable some deprecated methods of our parent class. """
        raise NotImplementedError

    def to_deprecated_son(self, prefix='', tag='i4x'):
        """ Disable some deprecated methods of our parent class. """
        raise NotImplementedError

    @classmethod
    def _from_deprecated_son(cls, id_dict, run):
        """ Disable some deprecated methods of our parent class. """
        raise NotImplementedError


class DefinitionLocator(Locator, DefinitionKey):
    """
    Container for how to locate a description (the course-independent content).
    """
    CANONICAL_NAMESPACE = 'def-v1'
    KEY_FIELDS = ('definition_id', 'block_type')
    CHECKED_INIT = False

    # override the abstractproperty
    block_type = None
    definition_id = None

    def __init__(self, block_type, definition_id, deprecated=False):    # pylint: disable=unused-argument
        if isinstance(definition_id, str):
            try:
                definition_id = self.as_object_id(definition_id)
            except ValueError as error:
                raise InvalidKeyError(DefinitionLocator, definition_id) from error
        super().__init__(definition_id=definition_id, block_type=block_type, deprecated=False)

    def _to_string(self):
        """
        Return a string representing this location.
        unicode(self) returns something like this: "519665f6223ebd6980884f2b+type+problem"
        """
        return f"{self.definition_id!s}+{self.BLOCK_TYPE_PREFIX}@{self.block_type}"

    URL_RE = re.compile(
        fr"^(?P<definition_id>[a-f0-9]+)\+{Locator.BLOCK_TYPE_PREFIX}"
        fr"@(?P<block_type>{Locator.ALLOWED_ID_CHARS}+)\Z",
        re.VERBOSE | re.UNICODE
    )

    @classmethod
    def _from_string(cls, serialized):
        """
        Return a DefinitionLocator parsing the given serialized string
        :param serialized: matches the string to
        """
        parse = cls.URL_RE.match(serialized)
        if not parse:
            raise InvalidKeyError(cls, serialized)

        parse = parse.groupdict()
        if parse['definition_id']:
            parse['definition_id'] = cls.as_object_id(parse['definition_id'])

        return cls(**{key: parse.get(key) for key in cls.KEY_FIELDS})

    @property
    def version(self):
        """
        Returns the ObjectId referencing this specific location.
        """
        return self.definition_id


class VersionTree:
    """
    Holds trees of Locators to represent version histories.
    """
    def __init__(self, locator, tree_dict=None):
        """
        :param locator: must be version specific (Course has version_guid or definition had id)
        """
        if not isinstance(locator, Locator) and not inspect.isabstract(locator):
            raise TypeError(f"locator {locator} must be a concrete subclass of Locator")
        version = ((hasattr(locator, 'version_guid') and locator.version_guid) or
                   (hasattr(locator, 'definition_id') and locator.definition_id))
        if not version:
            raise ValueError("locator must be version specific (Course has version_guid or definition had id)")
        self.locator = locator
        if tree_dict is None:
            self.children = []
        else:
            self.children = [VersionTree(child, tree_dict) for child in tree_dict.get(version, [])]


class AssetLocator(BlockUsageLocator, AssetKey):    # pylint: disable=abstract-method
    """
    An AssetKey implementation class.
    """
    CANONICAL_NAMESPACE = 'asset-v1'
    DEPRECATED_TAG = 'c4x'
    __slots__ = BlockUsageLocator.KEY_FIELDS

    ASSET_URL_RE = re.compile(r"""
        ^
        /c4x/
        (?P<org>[^/]+)/
        (?P<course>[^/]+)/
        (?P<category>[^/]+)/
        (?P<name>[^@]+)
        (@(?P<revision>[^/]+))?
        \Z
    """, re.VERBOSE)

    ALLOWED_ID_RE = BlockUsageLocator.DEPRECATED_ALLOWED_ID_RE
    # Allow empty asset ids. Used to generate a prefix url
    DEPRECATED_ALLOWED_ID_RE = re.compile(r'^' + Locator.DEPRECATED_ALLOWED_ID_CHARS + r'+\Z', re.UNICODE)

    @property
    def path(self):
        return self.block_id

    @property
    def asset_type(self):
        return self.block_type

    def replace(self, **kwargs):

        # `'path'` and `'asset_type'` are deprecated `KEY_FIELDS`.
        # Their values are reassigned to the new keys.
        if 'path' in kwargs and 'block_id' not in kwargs:
            kwargs['block_id'] = kwargs.pop('path')
        if 'asset_type' in kwargs and 'block_type' not in kwargs:
            kwargs['block_type'] = kwargs.pop('asset_type')
        return super().replace(**kwargs)

    def _to_deprecated_string(self):
        """
        Returns an old-style location, represented as:

        /c4x/org/course/category/name
        """
        # pylint: disable=missing-format-attribute
        url = (
            f"/{self.DEPRECATED_TAG}/{self.course_key.org}/{self.course_key.course}"
            f"/{self.block_type}/{self.block_id}"
        )
        if self.course_key.branch:
            url += f'@{self.course_key.branch}'
        return url

    @property
    def tag(self):
        """Returns the deprecated tag for this Location."""
        return self.DEPRECATED_TAG

    @classmethod
    def _from_deprecated_string(cls, serialized):
        match = cls.ASSET_URL_RE.match(serialized)
        if match is None:
            raise InvalidKeyError(cls, serialized)
        groups = match.groupdict()
        course_key = CourseLocator(
            groups['org'],
            groups['course'],
            None,
            groups.get('revision', None),
            deprecated=True
        )
        return cls(course_key, groups['category'], groups['name'], deprecated=True)

    def to_deprecated_list_repr(self):
        """
        Thumbnail locations are stored as lists [c4x, org, course, thumbnail, path, None] in contentstore.mongo
        That should be the only use of this method, but the method is general enough to provide the pre-opaque
        Location fields as an array in the old order with the tag.
        """
        return ['c4x', self.org, self.course, self.block_type, self.block_id, None]


# Register AssetLocator as the deprecated fallback for AssetKey
AssetKey.set_deprecated_fallback(AssetLocator)


class BundleDefinitionLocator(CheckFieldMixin, DefinitionKey):
    """
    Implementation of the DefinitionKey type, for XBlock content stored in
    Blockstore bundles. This is a low-level identifier used within the Open edX
    system for identifying and retrieving OLX.

    A "Definition" is a specific OLX file in a specific BundleVersion
    (or sometimes rather than a BundleVersion, it may point to a named draft.)
    The OLX file, and thus the definition key, defines Scope.content fields as
    well as defaults for Scope.settings and Scope.children fields. However the
    definition has no parent and no position in any particular course or other
    context - both of which require a *usage key* and not just a definition key.
    The same block definition (.olx file) can be used in multiple places in a
    course, each with a different usage key.

    Example serialized definition keys follow.

    The 'html' type OLX file "html/introduction/definition.xml" in bundle
    11111111-1111-1111-1111-111111111111, bundle version 5:

        bundle-olx:11111111-1111-1111-1111-111111111111:5:html:html/introduction/definition.xml

    The 'problem' type OLX file "problem324234.xml" in bundle
    22222222-2222-2222-2222-222222222222, draft 'studio-draft':

        bundle-olx:22222222-2222-2222-2222-222222222222:studio-draft:problem:problem/324234.xml

    (The serialized version is somewhat long and verbose because it should
    rarely be used except for debugging - the in-memory python key instance will
    be used most of the time, and users will rarely/never see definition keys.)

    User state should never be stored using a BundleDefinitionLocator as the
    key. State should always be stored against a usage locator, which refers to
    a particular definition being used in a particular context.

    Each BundleDefinitionLocator holds the following data
        1. Bundle UUID and [bundle version OR draft name]
        2. Block type (e.g. 'html', 'problem', etc.)
        3. Path to OLX file

    Note that since the data in an .olx file can only ever change in a bundle
    draft (not in a specific bundle version), an XBlock that is actively making
    changes to its Scope.content/Scope.settings field values must have a
    BundleDefinitionLocator with a draft name (not a bundle version).
    """
    CANONICAL_NAMESPACE = 'bundle-olx'
    KEY_FIELDS = ('bundle_uuid', 'block_type', 'olx_path', '_version_or_draft')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False
    OLX_PATH_REGEXP = re.compile(r'^[\w\-./]+$', flags=re.UNICODE)

    # pylint: disable=no-member

    def __init__(self, bundle_uuid, block_type, olx_path, bundle_version=None, draft_name=None, _version_or_draft=None):
        """
        Instantiate a new BundleDefinitionLocator
        """
        if not isinstance(bundle_uuid, UUID):
            bundle_uuid_str = bundle_uuid
            bundle_uuid = UUID(bundle_uuid_str)
            # Raise an error if this UUID is not in standard form, to prevent inconsistent UUID serialization
            # (Otherwise this class can fail the test_perturbed_serializations test when a UUID hyphen gets deleted)
            if bundle_uuid_str != str(bundle_uuid):
                raise InvalidKeyError(self.__class__, "bundle_uuid field got UUID string that's not in standard form")
        self._check_key_string_field("block_type", block_type)
        self._check_key_string_field("olx_path", olx_path, regexp=self.OLX_PATH_REGEXP)

        if (bundle_version is not None) + (draft_name is not None) + (_version_or_draft is not None) != 1:
            raise ValueError("Exactly one of [bundle_version, draft_name, _version_or_draft] must be specified")
        if _version_or_draft is not None:
            if isinstance(_version_or_draft, int):
                pass  # This is a bundle version number.
            else:
                # This is a draft name, not a bundle version:
                self._check_draft_name(_version_or_draft)
        elif draft_name is not None:
            self._check_draft_name(draft_name)
            _version_or_draft = draft_name
        else:
            assert isinstance(bundle_version, int)
            _version_or_draft = bundle_version

        super().__init__(
            bundle_uuid=bundle_uuid,
            block_type=block_type,
            olx_path=olx_path,
            _version_or_draft=_version_or_draft,
        )

    @property
    def bundle_version(self):
        """
        Get the Blockstore bundle version number, or None if a Blockstore draft
        name has been specified instead.
        """
        return self._version_or_draft if isinstance(self._version_or_draft, int) else None

    @property
    def draft_name(self):
        """
        Get the Blockstore draft name, or None if a Blockstore bundle version
        number has been specified instead.
        """
        return self._version_or_draft if not isinstance(self._version_or_draft, int) else None

    def _to_string(self):
        """
        Return a string representing this BundleDefinitionLocator
        """
        return ":".join((
            str(self.bundle_uuid), str(self._version_or_draft), self.block_type, self.olx_path,
        ))

    @classmethod
    def _from_string(cls, serialized):
        """
        Return a BundleDefinitionLocator by parsing the given serialized string
        """
        try:
            (bundle_uuid_str, _version_or_draft, block_type, olx_path) = serialized.split(':', 3)
        except ValueError as error:
            raise InvalidKeyError(cls, serialized) from error

        if _version_or_draft.isdigit():
            version_string = _version_or_draft
            _version_or_draft = int(version_string)
            if str(_version_or_draft) != version_string:
                # This inconsistent encoding can happen if the version number is prefixed with a zero e.g. ("05")
                raise InvalidKeyError(cls, serialized)

        try:
            return cls(
                bundle_uuid=bundle_uuid_str,
                block_type=block_type,
                olx_path=olx_path,
                _version_or_draft=_version_or_draft,
            )
        except (ValueError, TypeError) as error:
            raise InvalidKeyError(cls, serialized) from error

    @staticmethod
    def _check_draft_name(value):
        """
        Check that the draft name is valid (unambiguously not a bundle version
        number).

        Valid: studio_draft, foo-bar, import348975938
        Invalid: 1, 15, 873452847357834
        """
        if not isinstance(value, str) or not value:
            raise ValueError("Expected a non-empty string for draft name")
        if value.isdigit():
            raise ValueError("Cannot use an integer draft name as it conflicts with bundle version numbers")


class LibraryLocatorV2(CheckFieldMixin, LearningContextKey):
    """
    A key that represents a Blockstore-based content library.

    When serialized, these keys look like:
        lib:MITx:reallyhardproblems
        lib:hogwarts:p300-potions-exercises
    """
    CANONICAL_NAMESPACE = 'lib'
    KEY_FIELDS = ('org', 'slug')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    # Allow library slugs to contain unicode characters
    SLUG_REGEXP = re.compile(r'^[\w\-.]+$', flags=re.UNICODE)

    # pylint: disable=no-member

    def __init__(self, org, slug):
        """
        Construct a LibraryLocatorV2
        """
        self._check_key_string_field("org", org)
        self._check_key_string_field("slug", slug, regexp=self.SLUG_REGEXP)
        super().__init__(org=org, slug=slug)

    def _to_string(self):
        """
        Serialize this key as a string
        """
        return ":".join((self.org, self.slug))

    @classmethod
    def _from_string(cls, serialized):
        """
        Instantiate this key from a serialized string
        """
        try:
            (org, slug) = serialized.split(':')
            return cls(org=org, slug=slug)
        except (ValueError, TypeError) as error:
            raise InvalidKeyError(cls, serialized) from error

    def make_definition_usage(self, definition_key, usage_id=None):
        """
        Return a usage key, given the given the specified definition key and
        usage_id.
        """
        return LibraryUsageLocatorV2(
            lib_key=self,
            block_type=definition_key.block_type,
            usage_id=usage_id,
        )

    def for_branch(self, branch):
        """
        Compatibility helper.
        Some code calls .for_branch(None) on course keys. By implementing this,
        it improves backwards compatibility between library keys and course
        keys.
        """
        if branch is not None:
            raise ValueError("Cannot call for_branch on a content library key, except for_branch(None).")
        return self


class LibraryUsageLocatorV2(CheckFieldMixin, UsageKeyV2):
    """
    An XBlock in a Blockstore-based content library.

    When serialized, these keys look like:
        lb:MITx:reallyhardproblems:problem:problem1
    """
    CANONICAL_NAMESPACE = 'lb'  # "Library Block"
    KEY_FIELDS = ('lib_key', 'block_type', 'usage_id')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    # Allow usage IDs to contian unicode characters
    USAGE_ID_REGEXP = re.compile(r'^[\w\-.]+$', flags=re.UNICODE)

    # pylint: disable=no-member

    def __init__(self, lib_key, block_type, usage_id):
        """
        Construct a LibraryUsageLocatorV2
        """
        if not isinstance(lib_key, LibraryLocatorV2):
            raise TypeError("lib_key must be a LibraryLocatorV2")
        self._check_key_string_field("block_type", block_type)
        self._check_key_string_field("usage_id", usage_id, regexp=self.USAGE_ID_REGEXP)
        super().__init__(
            lib_key=lib_key,
            block_type=block_type,
            usage_id=usage_id,
        )

    @property
    def context_key(self):
        return self.lib_key

    @property
    def block_id(self):
        """
        Get the 'block ID' which is another name for the usage ID.
        """
        return self.usage_id

    def _to_string(self):
        """
        Serialize this key as a string
        """
        return ":".join((self.lib_key.org, self.lib_key.slug, self.block_type, self.usage_id))

    @classmethod
    def _from_string(cls, serialized):
        """
        Instantiate this key from a serialized string
        """
        try:
            (library_org, library_slug, block_type, usage_id) = serialized.split(':')
            lib_key = LibraryLocatorV2(library_org, library_slug)
            return cls(lib_key, block_type=block_type, usage_id=usage_id)
        except (ValueError, TypeError) as error:
            raise InvalidKeyError(cls, serialized) from error

    def html_id(self):
        """
        Return an id which can be used on an html page as an id attr of an html
        element. This is only in here for backwards-compatibility with XModules;
        don't use in new code.
        """
        warnings.warn(".html_id is deprecated", DeprecationWarning, stacklevel=2)
        # HTML5 allows ID values to contain any characters at all other than spaces.
        # These key types don't allow spaces either, so no transform is needed.
        return str(self)
