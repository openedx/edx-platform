"""
This module provides an abstraction for working with XModuleDescriptors
that are stored in a database an accessible using their Location as an identifier
"""

import re
from collections import namedtuple
from .exceptions import InvalidLocationError

URL_RE = re.compile("""
    (?P<tag>[^:]+)://
    (?P<org>[^/]+)/
    (?P<course>[^/]+)/
    (?P<category>[^/]+)/
    (?P<name>[^/]+)
    (/(?P<revision>[^/]+))?
    """, re.VERBOSE)

INVALID_CHARS = re.compile(r"[^\w.-]")

_LocationBase = namedtuple('LocationBase', 'tag org course category name revision')
class Location(_LocationBase):
    '''
    Encodes a location.

    Locations representations of URLs of the
    form {tag}://{org}/{course}/{category}/{name}[/{revision}]

    However, they can also be represented a dictionaries (specifying each component),
    tuples or list (specified in order), or as strings of the url
    '''
    __slots__ = ()

    @classmethod
    def clean(cls, value):
        """
        Return value, made into a form legal for locations
        """
        return re.sub('_+', '_', INVALID_CHARS.sub('_', value))

    def __new__(_cls, loc_or_tag, org=None, course=None, category=None, name=None, revision=None):
        """
        Create a new location that is a clone of the specifed one.

        location - Can be any of the following types:
            string: should be of the form {tag}://{org}/{course}/{category}/{name}[/{revision}]
            list: should be of the form [tag, org, course, category, name, revision]
            dict: should be of the form {
                'tag': tag,
                'org': org,
                'course': course,
                'category': category,
                'name': name,
                'revision': revision,
            }
            Location: another Location object

        In both the dict and list forms, the revision is optional, and can be ommitted.

        Components must be composed of alphanumeric characters, or the characters '_', '-', and '.'

        Components may be set to None, which may be interpreted by some contexts to mean
        wildcard selection
        """

        if org is None and course is None and category is None and name is None and revision is None:
            location = loc_or_tag
        else:
            location = (loc_or_tag, org, course, category, name, revision)

        def check_dict(dict_):
            check_list(dict_.values())

        def check_list(list_):
            for val in list_:
                if val is not None and INVALID_CHARS.search(val) is not None:
                    raise InvalidLocationError(location)

        if isinstance(location, basestring):
            match = URL_RE.match(location)
            if match is None:
                raise InvalidLocationError(location)
            else:
                groups = match.groupdict()
                check_dict(groups)
                return _LocationBase.__new__(_cls, **groups)
        elif isinstance(location, (list, tuple)):
            if len(location) not in (5, 6):
                raise InvalidLocationError(location)

            if len(location) == 5:
                args = tuple(location) + (None, )
            else:
                args = tuple(location)

            check_list(args)
            return _LocationBase.__new__(_cls, *args)
        elif isinstance(location, dict):
            kwargs = dict(location)
            kwargs.setdefault('revision', None)

            check_dict(kwargs)
            return _LocationBase.__new__(_cls, **kwargs)
        elif isinstance(location, Location):
            return _LocationBase.__new__(_cls, location)
        else:
            raise InvalidLocationError(location)

    def url(self):
        """
        Return a string containing the URL for this location
        """
        url = "{tag}://{org}/{course}/{category}/{name}".format(**self.dict())
        if self.revision:
            url += "/" + self.revision
        return url

    def html_id(self):
        """
        Return a string with a version of the location that is safe for use in html id attributes
        """
        return "-".join(str(v) for v in self.list() if v is not None).replace('.', '_')

    def dict(self):
        return self.__dict__

    def list(self):
        return list(self)

    def __str__(self):
        return self.url()

    def __repr__(self):
        return "Location%s" % repr(tuple(self))


class ModuleStore(object):
    """
    An abstract interface for a database backend that stores XModuleDescriptor instances
    """
    def get_item(self, location, default_class=None):
        """
        Returns an XModuleDescriptor instance for the item at location.
        If location.revision is None, returns the item with the most
        recent revision

        If any segment of the location is None except revision, raises
            xmodule.modulestore.exceptions.InsufficientSpecificationError
        If no object is found at that location, raises xmodule.modulestore.exceptions.ItemNotFoundError

        location: Something that can be passed to Location
        default_class: An XModuleDescriptor subclass to use if no plugin matching the
            location is found
        """
        raise NotImplementedError
    
    def get_items(self, location, default_class=None):
        """
        Returns a list of XModuleDescriptor instances for the items
        that match location. Any element of location that is None is treated
        as a wildcard that matches any value

        location: Something that can be passed to Location
        default_class: An XModuleDescriptor subclass to use if no plugin matching the
            location is found
        """
        raise NotImplementedError

    # TODO (cpennington): Replace with clone_item
    def create_item(self, location, editor):
        raise NotImplementedError

    def update_item(self, location, data):
        """
        Set the data in the item specified by the location to
        data

        location: Something that can be passed to Location
        data: A nested dictionary of problem data
        """
        raise NotImplementedError

    def update_children(self, location, children):
        """
        Set the children for the item specified by the location to
        children

        location: Something that can be passed to Location
        children: A list of child item identifiers
        """
        raise NotImplementedError

    def update_metadata(self, location, metadata):
        """
        Set the metadata for the item specified by the location to
        metadata

        location: Something that can be passed to Location
        metadata: A nested dictionary of module metadata
        """
        raise NotImplementedError
