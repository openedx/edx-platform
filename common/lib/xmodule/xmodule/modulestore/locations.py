""" Contains Locations ___ """

import urllib
import re
from collections import namedtuple

from xmodule.modulestore.exceptions import InvalidLocationError
from xmodule.modulestore.keys import CourseKey, UsageKey

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
    def __init__(self, org, course, run):
        self._org = org
        self._course = course
        self._run = run

    @classmethod
    def _from_string(cls, serialized):
        # Turns encoded slashes into actual slashes
        return cls(*serialized.split('/'))

    def _to_string(self):
        # Turns slashes into encoded slashes
        return self.to_deprecated_string()

    @property
    def org(self):
        return self._org

    @property
    def course(self):
        return self._course

    @property
    def run(self):
        return self._run

    @property
    def offering(self):
        return '/'.join([self._course, self._run])

    def make_asset_key(self, path):
        return Location('c4x', self._org, self._course, 'asset', path)

    def make_usage_key(self, block_type, name):
        return Location('i4x', self._org, self._course, block_type, name)

    def to_deprecated_string(self):
        return '/'.join([self._org, self._course, self._run])


def _check_location_part(val, regexp):
    """
    Check that `regexp` doesn't match inside `val`. If it does, raise an exception

    Args:
        val (string): The value to check
        regexp (re.RegexObject): The regular expression specifying invalid characters

    Raises:
        InvalidLocationError: Raised if any invalid character is found in `val`
    """
    if val is not None and regexp.search(val) is not None:
        raise InvalidLocationError("Invalid characters in {!r}.".format(val))


class Location(UsageKey, namedtuple('LocationBase', 'tag org course run category name revision')):
    """
    Encodes a location.

    Locations representations of URLs of the
    form {tag}://{org}/{course}/{category}/{name}[@{revision}], situated in the course
    {org}/{course}/{run}.
    """
    __slots__ = ()

    @staticmethod
    def _clean(value, invalid):
        """
        invalid should be a compiled regexp of chars to replace with '_'
        """
        return re.sub('_+', '_', invalid.sub('_', value))

    @staticmethod
    def clean(value):
        """
        Return value, made into a form legal for locations
        """
        return Location._clean(value, INVALID_CHARS)

    @staticmethod
    def clean_keeping_underscores(value):
        """
        Return value, replacing INVALID_CHARS, but not collapsing multiple '_' chars.
        This for cleaning asset names, as the YouTube ID's may have underscores in them, and we need the
        transcript asset name to match. In the future we may want to change the behavior of _clean.
        """
        return INVALID_CHARS.sub('_', value)

    @staticmethod
    def clean_for_url_name(value):
        """
        Convert value into a format valid for location names (allows colons).
        """
        return Location._clean(value, INVALID_CHARS_NAME)

    @staticmethod
    def clean_for_html(value):
        """
        Convert a string into a form that's safe for use in html ids, classes, urls, etc.
        Replaces all INVALID_HTML_CHARS with '_', collapses multiple '_' chars
        """
        return Location._clean(value, INVALID_HTML_CHARS)

    @staticmethod
    def is_valid(value):
        '''
        Check if the value is a valid location, in any acceptable format.
        '''
        try:
            Location(value)
        except InvalidLocationError:
            return False
        return True

    @staticmethod
    def ensure_fully_specified(location):
        '''Make sure location is valid, and fully specified.  Raises
        InvalidLocationError or InsufficientSpecificationError if not.

        returns a Location object corresponding to location.
        '''
        loc = Location(location)
        for key, val in loc.dict().iteritems():
            if key != 'revision' and val is None:
                raise InsufficientSpecificationError(location)
        return loc

    def __new__(_cls, tag=None, org=None, course=None, run=None, category=None,
                name=None, revision=None):
        """
        Create a new Location that is a clone of the specifed one.

        Components must be composed of alphanumeric characters, or the
        characters '_', '-', and '.'.  The name component is additionally allowed to have ':',
        which is interpreted specially for xml storage.

        Components may be set to None, which may be interpreted in some contexts
        to mean wildcard selection.
        """

        for part in (tag, org, course, run, category, revision):
            _check_location_part(part, INVALID_CHARS)
        _check_location_part(name, INVALID_CHARS_NAME)

        return super(_cls, Location).__new__(_cls, tag, org, course, run, category, name, revision)

    @classmethod
    def from_deprecated_strings(cls, course_id, location):
        course_id = SlashSeparatedCourseKey._from_string(course_id)

        match = URL_RE.match(location)
        if match is None:
            log.debug(u"location %r doesn't match URL", location)
            raise InvalidKeyError(location)
        groups = match.groupdict()
        return cls(run=course_id.run, **groups)

    def url(self):
        """
        Return a string containing the URL for this location
        """
        return self.to_deprecated_string()

    def to_deprecated_string(self):
        url = u"{0.tag}://{0.org}/{0.course}/{0.category}/{0.name}".format(self)
        if self.revision:
            url += u"@{rev}".format(rev=self.revision)  # pylint: disable=E1101
        return url

    def html_id(self):
        """
        Return a string with a version of the location that is safe for use in
        html id attributes
        """
        id_fields = [self.tag, self.org, self.course, self.category, self.name, self.revision]
        id_string = u"-".join([v for v in id_fields if v is not None])
        return Location.clean_for_html(id_string)

    def course_key(self):
        return SlashSeparatedCourseKey(self.org, self.course, self.run)
