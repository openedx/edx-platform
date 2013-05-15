"""
Created on Mar 13, 2013

@author: dmitchell
"""
from __future__ import absolute_import
import re
import logging
from xmodule.modulestore.exceptions import InvalidLocationError, \
    InsufficientSpecificationError
from django.utils import http

log = logging.getLogger(__name__)


# TODO how to keep this from being instantiated but not fail subclass inits?
class Locator(object):
    def url(self):
        """
        Return a string containing the URL for this location. Raises
        InsufficientSpecificationError if the instance doesn't have a
        complete enough specification to generate a url
        """
        raise InsufficientSpecificationError()

    def html_id(self):
        """
        Return a string with a version of the location that is safe for use in
        html id attributes
        """
        # dhm: seems wrong to me to have the DAO worry about client
        # representations and escaping. Is urlquote overkill? (converts
        # @ sign too :-(
        return http.urlquote(self.url())

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return self.url()


class CourseLocator(Locator):
    """
    Should have at lease a specific course_id (id for the course as if it were a project w/
    versions) with optional 'revision' (must be 'draft', 'published', or None),
    or version_guid (which points to a specific version). Can contain both in which case
    the persistence layer may raise exceptions if the given version != the current such version
    of the course.
    """
    SPECIFIC_VERSION = 'cvx'
    RUN_TRACKING_VERSION = 'crx'

    _URN_RE_ = re.compile("""
    (?P<tag>crx|cvx):?//?
    (?P<identifier>[^/@]+)(@(?P<revision>[^/]+))?
    """, re.VERBOSE)

    def __init__(self, *fields, **kwargs):
        def _parse_init_arg(arg):
            if 'version_guid' in arg:
                self.version_guid = arg['version_guid']
            if 'course_id' in arg:
                self.course_id = arg['course_id']
            if 'revision' in arg:
                self.revision = arg['revision']

        # init fields so they're all defined
        self.version_guid = self.course_id = self.revision = None

        # first arg can be a url
        if len(fields) > 0:
            if isinstance(fields[0], basestring):
                val = http.urlunquote(fields[0])
                match = self._URN_RE_.match(val)
                if match is None:
                    log.debug('location is instance of %s but no URL match'
                        % basestring)
                    raise InvalidLocationError(val)
                urnfields = match.groupdict()
                if urnfields['tag'] == self.SPECIFIC_VERSION:
                    self.version_guid = urnfields['identifier']
                else:
                    self.course_id = urnfields['identifier']
                    if 'revision' in urnfields:
                        self.revision = urnfields['revision']
            elif isinstance(fields[0], CourseLocator):
                self.__dict__.update(fields[0].__dict__)

        for arg in fields:
            if isinstance(arg, CourseLocator):
                _parse_init_arg(arg.__dict__)
            elif isinstance(arg, dict):
                _parse_init_arg(arg)
        _parse_init_arg(kwargs)

    def _ensure_fully_specified(self):
        """
        Make sure this object is valid, and fully specified.
        Returns True or False.
        """
        return self.version_guid is not None or self.course_id is not None

    def url(self):
        if self.version_guid is not None:
            return self.SPECIFIC_VERSION + '/' + str(self.version_guid)
        elif self.revision is not None:
            return (self.RUN_TRACKING_VERSION + '/' + self.course_id + '@'
                + self.revision)
        elif self.course_id is not None:
            return self.RUN_TRACKING_VERSION + '/' + self.course_id
        else:
            # TODO should this raise an error, return empty string, or None?
            return ""

    def __repr__(self):
        return 'CourseLocator(%s)' % repr(self.__dict__)

    def version(self):
        return self.version_guid


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
    _I4X_RE_ = re.compile("""
        i4x:?//?
        (?P<org>[^/]+)/
        (?P<course>[^/]+)/
        (?P<category>[^/]+)/
        (?P<name>[^@]+)
        (@(?P<revision>[^/]+))?
        """, re.VERBOSE)

    _URN_RE_ = re.compile("""
    (?P<tag>crx|cvx):?//?
    (?P<identifier>[^/@]+)(@(?P<revision>[^/]+))?/?
    (?P<usage_id>[^/]+)?
    """, re.VERBOSE)

    def __init__(self, *structured_loc, **kwargs):
        """
        Create a new location that is a clone of the specified one.

        first arg - Can be any of the following types:
            string: should be of the form
                    crx/{course_id}[@{revision}]/usage_id
                    cvx/version_id/usage_id

            dict or keywords: should be of the form {
                'version_guid' : uniqueid mutually exclusive w/ course_id,
                'course_id' : uniqueid alternative to version_guid,
                'usage_id' : guid,
                'revision': 'draft' | 'published' (optional only applies for
                    course_id),
            }
            BlockUsageLocator: another BlockUsageLocator object
        """
        fields = {}

        if len(structured_loc) == 0:
            pass
        elif isinstance(structured_loc[0], basestring):
            val = http.urlunquote(structured_loc[0])
            match = self._URN_RE_.match(val)
            if match is None:
                log.debug('location is instance of %s but no URL match'
                    % basestring)
                raise InvalidLocationError(val)
            urnfields = match.groupdict()
            if urnfields['tag'] == self.SPECIFIC_VERSION:
                fields['version_guid'] = urnfields['identifier']
            else:
                fields['course_id'] = urnfields['identifier']
                if 'revision' in urnfields:
                    fields['revision'] = urnfields['revision']
            fields['usage_id'] = urnfields['usage_id']

        elif isinstance(structured_loc[0], dict):
            fields = structured_loc[0]

        elif isinstance(structured_loc[0], CourseLocator):
            fields = structured_loc[0].__dict__.copy()

        for struct in structured_loc[1:]:
            fields.update(struct if isinstance(struct, dict)
                else struct.__dict__)

        fields.update(kwargs)

        super(BlockUsageLocator, self).__init__(fields)
        # TODO should it be an error if block is unspecified or is
        # ensure_fully_specified sufficient for this case?
        self.usage_id = fields.get('usage_id')

    @staticmethod
    def ensure_fully_specified(location):
        """
        Make sure location is valid, and fully specified.  Raises
        InvalidLocationError or InsufficientSpecificationError if not.

        returns a BlockUsageLocator object corresponding to location.
        NOTE: this function is not as flexible as the class constructor. It
        does not accept kwargs nor overrides. Replace uses of this which intend
        it to only give an instance if the model is well-formed with
        BlockUsageLocator.ensure_fully_specified(BlockUsageLocator(args..))
        """
        if isinstance(location, BlockUsageLocator):
            loc = location
        else:
            loc = BlockUsageLocator(location)

        if not super(BlockUsageLocator, loc)._ensure_fully_specified():
            raise InsufficientSpecificationError(location)
        if loc.usage_id is None:
            raise InsufficientSpecificationError(location)
        return loc

    def replace(self, **kwargs):
        """
        Return a new Location instance which is a copy of this one except for
        overrides in the arg list.
        """
        return BlockUsageLocator(self, kwargs)

    def url(self):
        """
        Return a string containing the URL for this location
        """
        return (super(BlockUsageLocator, self).url() + '/' +
            (self.usage_id or ''))

    def __repr__(self):
        return "BlockUsageLocator(%s)" % repr(self.__dict__)


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
