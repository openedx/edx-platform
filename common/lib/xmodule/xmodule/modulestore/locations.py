""" Contains Locations ___ """

import logging
import re
from collections import namedtuple
from opaque_keys import InvalidKeyError

from xmodule.modulestore.keys import CourseKey, UsageKey, DefinitionKey, AssetKey

log = logging.getLogger(__name__)

URL_RE = re.compile("""
    (?P<tag>[^:]+)://?
    (?P<org>[^/]+)/
    (?P<course>[^/]+)/
    (?P<category>[^/]+)/
    (?P<name>[^@]+)
    (@(?P<revision>[^/]+))?
    """, re.VERBOSE)

# TODO (cpennington): We should decide whether we want to expand the
# list of valid characters in a location
INVALID_CHARS = re.compile(r"[^\w.%-]", re.UNICODE)
# Names are allowed to have colons.
INVALID_CHARS_NAME = re.compile(r"[^\w.:%-]", re.UNICODE)

# html ids can contain word chars and dashes
INVALID_HTML_CHARS = re.compile(r"[^\w-]", re.UNICODE)


class SlashSeparatedCourseKey(CourseKey):
    """Course key for old style org/course/run course identifiers"""

    CANONICAL_NAMESPACE = 'slashes'
    KEY_FIELDS = ('org', 'course', 'run')
    __slots__ = KEY_FIELDS

    @classmethod
    def _from_string(cls, serialized):
        # Turns encoded slashes into actual slashes
        return cls(*serialized.split('/'))

    def _to_string(self):
        # Turns slashes into encoded slashes
        return self.to_deprecated_string()

    @property
    def offering(self):
        return '/'.join([self.course, self.run])

    def make_asset_key(self, asset_type, path):
        return AssetLocation(self.org, self.course, self.run, asset_type, path, None)

    def make_usage_key(self, block_type, name):
        return Location(self.org, self.course, self.run, block_type, name, None)

    def to_deprecated_string(self):
        return '/'.join([self.org, self.course, self.run])

    def make_usage_key_from_deprecated_string(self, location_url):
        """
        Temporary mechanism for creating a UsageKey given a CourseKey and a serialized Location. NOTE:
        this prejudicially takes the tag, org, and course from the url not self.

        Raises:
            InvalidKeyError: if the url does not parse
        """
        match = URL_RE.match(location_url)
        if match is None:
            log.debug(u"location %r doesn't match URL", location_url)
            raise InvalidKeyError(location_url)
        groups = match.groupdict()
        if 'tag' in groups:
            del groups['tag']
        return Location(run=self.run, **groups)


def _check_location_part(val, regexp):
    """
    Check that `regexp` doesn't match inside `val`. If it does, raise an exception

    Args:
        val (string): The value to check
        regexp (re.RegexObject): The regular expression specifying invalid characters

    Raises:
        InvalidKeyError: Raised if any invalid character is found in `val`
    """
    if val is None:
        return

    if not isinstance(val, basestring):
        raise InvalidKeyError("{!r} is not a string".format(val))

    if regexp.search(val) is not None:
        raise InvalidKeyError("Invalid characters in {!r}.".format(val))


class LocationBase(object):
    """
    Encodes a location.

    Locations representations of URLs of the
    form {tag}://{org}/{course}/{category}/{name}[@{revision}], situated in the course
    {org}/{course}/{run}.
    """
    KEY_FIELDS = ('org', 'course', 'run', 'category', 'name', 'revision')

    @classmethod
    def _clean(cls, value, invalid):
        """
        invalid should be a compiled regexp of chars to replace with '_'
        """
        return re.sub('_+', '_', invalid.sub('_', value))

    @classmethod
    def clean(cls, value):
        """
        Return value, made into a form legal for locations
        """
        return cls._clean(value, INVALID_CHARS)

    @classmethod
    def clean_keeping_underscores(cls, value):
        """
        Return value, replacing INVALID_CHARS, but not collapsing multiple '_' chars.
        This for cleaning asset names, as the YouTube ID's may have underscores in them, and we need the
        transcript asset name to match. In the future we may want to change the behavior of _clean.
        """
        return INVALID_CHARS.sub('_', value)

    @classmethod
    def clean_for_url_name(cls, value):
        """
        Convert value into a format valid for location names (allows colons).
        """
        return cls._clean(value, INVALID_CHARS_NAME)

    @classmethod
    def clean_for_html(cls, value):
        """
        Convert a string into a form that's safe for use in html ids, classes, urls, etc.
        Replaces all INVALID_HTML_CHARS with '_', collapses multiple '_' chars
        """
        return cls._clean(value, INVALID_HTML_CHARS)

    def __init__(self, org, course, run, category, name, revision=None):
        """
        Create a new Location that is a clone of the specifed one.

        Components must be composed of alphanumeric characters, or the
        characters '_', '-', and '.'.  The name component is additionally allowed to have ':',
        which is interpreted specially for xml storage.

        Components may be set to None, which may be interpreted in some contexts
        to mean wildcard selection.
        """

        for part in (org, course, run, category, revision):
            _check_location_part(part, INVALID_CHARS)
        _check_location_part(name, INVALID_CHARS_NAME)

        return super(LocationBase, self).__init__(org, course, run, category, name, revision)

    @property
    def definition_key(self):
        # Locations are both UsageKeys and DefinitionKeys
        return self

    @property
    def block_type(self):
        return self.category

    def url(self):
        """
        Return a string containing the URL for this location
        """
        return self.to_deprecated_string()

    def to_deprecated_string(self):
        url = u"{0.DEPRECATED_TAG}://{0.org}/{0.course}/{0.category}/{0.name}".format(self)
        if self.revision:
            url += u"@{rev}".format(rev=self.revision)  # pylint: disable=E1101
        return url

    def _to_string(self):
        output = u"/".join(
            unicode(val)
            for val in (self.org, self.course, self.run, self.category, self.name)
        )
        if self.revision:
            output += u'@{}'.format(self.revision)
        return output

    @classmethod
    def _from_string(cls, serialized):

        pattern = """
            (?P<org>[^/]+)/
            (?P<course>[^/]+)/
            (?P<run>[^/]+)/
            (?P<category>[^/]+)/
            (?P<name>[^@]+)
            (@(?P<revision>[^/]+))?
        """

        match = re.match(pattern, serialized, re.VERBOSE)
        if not match:
            raise InvalidKeyError(serialized)

        return cls(**match.groupdict())

    def html_id(self):
        """
        Return a string with a version of the location that is safe for use in
        html id attributes
        """
        id_fields = [self.DEPRECATED_TAG, self.org, self.course, self.category, self.name, self.revision]
        id_string = u"-".join([v for v in id_fields if v is not None])
        return Location.clean_for_html(id_string)

    @property
    def course_key(self):
        return SlashSeparatedCourseKey(self.org, self.course, self.run)


class Location(LocationBase, UsageKey, DefinitionKey):
    CANONICAL_NAMESPACE = 'location'
    DEPRECATED_TAG = 'i4x'
    __slots__ = LocationBase.KEY_FIELDS


class AssetLocation(LocationBase, AssetKey):
    CANONICAL_NAMESPACE = 'asset-location'
    DEPRECATED_TAG = 'c4x'
    __slots__ = LocationBase.KEY_FIELDS

    def __init__(self, org, course, run, asset_type, path, revision=None):
        super(AssetLocation, self).__init__(org, course, run, asset_type, path, revision)

    @property
    def path(self):
        return self.name
