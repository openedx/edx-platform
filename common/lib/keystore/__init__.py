"""
This module provides an abstraction for working objects that conceptually have
the following attributes:

    location: An identifier for an item, of which there might be many revisions
    children: A list of urls for other items required to fully define this object
    data: A set of nested data needed to define this object
    editor: The editor/owner of the object
    parents: Url pointers for objects that this object was derived from
    revision: What revision of the item this is
"""

import re
from .exceptions import InvalidLocationError

URL_RE = re.compile("""
    (?P<tag>[^:]+)://
    (?P<org>[^/]+)/
    (?P<course>[^/]+)/
    (?P<category>[^/]+)/
    (?P<name>[^/]+)
    (/(?P<revision>[^/]+))?
    """, re.VERBOSE)


class Location(object):
    '''
    Encodes a location.

    Locations representations of URLs of the
    form {tag}://{org}/{course}/{category}/{name}[/{revision}]

    However, they can also be represented a dictionaries (specifying each component),
    tuples or list (specified in order), or as strings of the url
    '''
    def __init__(self, location):
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

        None of the components of a location may contain the '/' character
        """
        self.update(location)

    def update(self, location):
        """
        Update this instance with data from another Location object.

        location: can take the same forms as specified by `__init__`
        """
        self.tag = self.org = self.course = self.category = self.name = self.revision = None

        if isinstance(location, basestring):
            match = URL_RE.match(location)
            if match is None:
                raise InvalidLocationError(location)
            else:
                self.update(match.groupdict())
        elif isinstance(location, list):
            if len(location) not in (5, 6):
                raise InvalidLocationError(location)

            (self.tag, self.org, self.course, self.category, self.name) = location[0:5]
            self.revision = location[5] if len(location) == 6 else None
        elif isinstance(location, dict):
            try:
                self.tag = location['tag']
                self.org = location['org']
                self.course = location['course']
                self.category = location['category']
                self.name = location['name']
            except KeyError:
                raise InvalidLocationError(location)
            self.revision = location.get('revision')
        elif isinstance(location, Location):
            self.update(location.list())
        else:
            raise InvalidLocationError(location)

        for val in self.list():
            if val is not None and '/' in val:
                raise InvalidLocationError(location)

    def __str__(self):
        return self.url()

    def url(self):
        """
        Return a string containing the URL for this location
        """
        url = "{tag}://{org}/{course}/{category}/{name}".format(**self.dict())
        if self.revision:
            url += "/" + self.revision
        return url

    def list(self):
        """
        Return a list representing this location
        """
        return [self.tag, self.org, self.course, self.category, self.name, self.revision]

    def dict(self):
        """
        Return a dictionary representing this location
        """
        return {'tag': self.tag,
                'org': self.org,
                'course': self.course,
                'category': self.category,
                'name': self.name,
                'revision': self.revision}


class KeyStore(object):
    def get_item(self, location):
        """
        Returns an XModuleDescriptor instance for the item at location

        If no object is found at that location, raises keystore.exceptions.ItemNotFoundError

        Searches for all matches of a partially specifed location, but raises an
        keystore.exceptions.InsufficientSpecificationError if more
        than a single object matches the query.

        location: Something that can be passed to Location
        """
        raise NotImplementedError

    def create_item(self, location, editor):
        """
        Create an empty item at the specified location with the supplied editor

        location: Something that can be passed to Location
        """
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
        data

        location: Something that can be passed to Location
        children: A list of child item identifiers
        """
        raise NotImplementedError
