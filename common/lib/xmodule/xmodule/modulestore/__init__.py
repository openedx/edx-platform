"""
This module provides an abstraction for working with XModuleDescriptors
that are stored in a database an accessible using their Location as an identifier
"""

import logging
from xmodule.errortracker import make_error_tracker
from bson.son import SON

log = logging.getLogger('mitx.' + 'modulestore')



# FIXME remove
class Location(object):
    pass

class ModuleStore(object):
    """
    An abstract interface for a database backend that stores XModuleDescriptor
    instances
    """
    def has_item(self, location):
        """
        Returns True if location exists in this ModuleStore.
        """
        raise NotImplementedError

    def get_item(self, location, depth=0):
        """
        Returns an XModuleDescriptor instance for the item at location.

        If any segment of the location is None except revision, raises
            xmodule.modulestore.exceptions.InsufficientSpecificationError

        If no object is found at that location, raises
            xmodule.modulestore.exceptions.ItemNotFoundError

        location: Something that can be passed to Location

        depth (int): An argument that some module stores may use to prefetch
            descendents of the queried modules for more efficient results later
            in the request. The depth is counted in the number of calls to
            get_children() to cache. None indicates to cache all descendents
        """
        raise NotImplementedError

    def get_instance(self, course_id, location, depth=0):
        """
        Get an instance of this location, with policy for course_id applied.
        TODO (vshnayder): this may want to live outside the modulestore eventually
        """
        raise NotImplementedError

    def get_item_errors(self, location):
        """
        Return a list of (msg, exception-or-None) errors that the modulestore
        encountered when loading the item at location.

        location : something that can be passed to Location

        Raises the same exceptions as get_item if the location isn't found or
        isn't fully specified.
        """
        raise NotImplementedError

    def get_items(self, locator, qualifiers):
        """
        Returns a list of XModuleDescriptor instances for the items
        that match location. Any element of location that is None is treated
        as a wildcard that matches any value

        location: Something that can be passed to Location

        depth: An argument that some module stores may use to prefetch
            descendents of the queried modules for more efficient results later
            in the request. The depth is counted in the number of calls to
            get_children() to cache. None indicates to cache all descendents
        """
        raise NotImplementedError

    def clone_item(self, source_id, destination_id, source, location):
        """
        Clone a new item that is a copy of the item at the location `source`
        and writes it to `location`
        """
        raise NotImplementedError

    def update_item(self, course_id, location, data):
        """
        Set the data in the item specified by the location to
        data

        course_id: Id of the course this item is in
        location: Something that can be passed to Location
        data: A nested dictionary of problem data
        """
        raise NotImplementedError

    def update_children(self, course_id, location, children):
        """
        Set the children for the item specified by the location to
        children

        location: Something that can be passed to Location
        children: A list of child item identifiers
        """
        raise NotImplementedError

    def update_metadata(self, course_id, location, metadata):
        """
        Set the metadata for the item specified by the location to
        metadata

        location: Something that can be passed to Location
        metadata: A nested dictionary of module metadata
        """
        raise NotImplementedError

    def delete_item(self, usage_locator, user_id, force=False):
        """
        Delete an item from this modulestore

        location: Something that can be passed to Location
        """
        raise NotImplementedError

    def get_courses(self, revision, qualifiers=None):
        '''
        Returns a list containing the top level XModuleDescriptors of the courses
        in this modulestore.

        The list of courses is
        filtered to only match courses with those specified qualifiers and revisions.
        '''
        raise NotImplementedError

    def get_course(self, course_id):
        '''
        Look for a specific course id.  Returns the course descriptor, or None if not found.
        '''
        raise NotImplementedError

    def get_parent_locations(self, locator, usage_id=None):
        '''Find all locations that are the parents of this location in this
        course.  Needed for path_to_location().

        returns an iterable of things that can be passed to Location.
        '''
        raise NotImplementedError

    def get_errored_courses(self):
        """
        This function doesn't make sense for the mongo modulestore, as courses
        are loaded on demand, rather than up front
        """
        raise NotImplementedError


class ModuleStoreBase(ModuleStore):
    '''
    Implement interface functionality that can be shared.
    '''
    def __init__(self):
        '''
        Set up the error-tracking logic.
        '''
        self._location_errors = {}  # location -> ErrorLog

    def _get_errorlog(self, location):
        """
        If we already have an errorlog for this location, return it.  Otherwise,
        create one.
        """
        location = Location(location)
        if location not in self._location_errors:
            self._location_errors[location] = make_error_tracker()
        return self._location_errors[location]

    def get_item_errors(self, location):
        """
        Return list of errors for this location, if any.  Raise the same
        errors as get_item if location isn't present.

        NOTE: For now, the only items that track errors are CourseDescriptors in
        the xml datastore.  This will return an empty list for all other items
        and datastores.
        """
        # check that item is present and raise the promised exceptions if needed
        # TODO (vshnayder): post-launch, make errors properties of items
        # self.get_item(location)

        errorlog = self._get_errorlog(location)
        return errorlog.errors

    def get_course(self, course_id):
        """Default impl--linear search through course list"""
        for c in self.get_courses('published'):
            if c.id == course_id:
                return c
        return None


def namedtuple_to_son(namedtuple, prefix=''):
    """
    Converts a namedtuple into a SON object with the same key order
    """
    son = SON()
    for idx, field_name in enumerate(namedtuple._fields):
        son[prefix + field_name] = namedtuple[idx]
    return son
