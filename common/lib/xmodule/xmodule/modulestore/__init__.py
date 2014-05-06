"""
This module provides an abstraction for working with XModuleDescriptors
that are stored in a database an accessible using their Location as an identifier
"""

import logging
import re

from collections import namedtuple, defaultdict
import collections

from abc import ABCMeta, abstractmethod
from xblock.plugin import default_select

from .exceptions import InvalidLocationError, InsufficientSpecificationError
from xmodule.errortracker import make_error_tracker
from xmodule.modulestore.keys import CourseKey, UsageKey
from xmodule.modulestore.locations import Location  # For import backwards compatibility
from opaque_keys import InvalidKeyError
from xmodule.modulestore.locations import SlashSeparatedCourseKey
from xblock.runtime import Mixologist
from xblock.core import XBlock
import datetime

log = logging.getLogger('edx.modulestore')

SPLIT_MONGO_MODULESTORE_TYPE = 'split'
MONGO_MODULESTORE_TYPE = 'mongo'
XML_MODULESTORE_TYPE = 'xml'


class ModuleStoreRead(object):
    """
    An abstract interface for a database backend that stores XModuleDescriptor
    instances and extends read-only functionality
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def has_item(self, usage_key):
        """
        Returns True if usage_key exists in this ModuleStore.
        """
        pass

    @abstractmethod
    def get_item(self, usage_key, depth=0):
        """
        Returns an XModuleDescriptor instance for the item at location.

        If any segment of the location is None except revision, raises
            xmodule.modulestore.exceptions.InsufficientSpecificationError

        If no object is found at that location, raises
            xmodule.modulestore.exceptions.ItemNotFoundError

        usage_key: A :class:`.UsageKey` subclass instance

        depth (int): An argument that some module stores may use to prefetch
            descendents of the queried modules for more efficient results later
            in the request. The depth is counted in the number of calls to
            get_children() to cache. None indicates to cache all descendents
        """
        pass

    @abstractmethod
    def get_course_errors(self, course_id):
        """
        Return a list of (msg, exception-or-None) errors that the modulestore
        encountered when loading the course at course_id.

        Raises the same exceptions as get_item if the location isn't found or
        isn't fully specified.

        Args:
            course_id (:class:`.CourseKey`): The course to check for errors
        """
        pass

    @abstractmethod
    def get_items(self, location, course_id=None, depth=0, qualifiers=None):
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
        pass

    def _block_matches(self, fields_or_xblock, qualifiers):
        '''
        Return True or False depending on whether the field value (block contents)
        matches the qualifiers as per get_items. Note, only finds directly set not
        inherited nor default value matches.
        For substring matching pass a regex object.
        for arbitrary function comparison such as date time comparison, pass
        the function as in start=lambda x: x < datetime.datetime(2014, 1, 1, 0, tzinfo=pytz.UTC)

        Args:
            fields (dict): either the json blob (from the db or get_explicitly_set_fields)
                or the xblock.fields() value
             qualifiers (dict): field: searchvalue pairs.
        '''
        if isinstance(fields_or_xblock, XBlock):
            fields = fields_or_xblock.fields
            xblock = fields_or_xblock
            is_xblock = True
        else:
            fields = fields_or_xblock
            is_xblock = False

        def _is_set_on(key):
            """
            Is this key set in fields? (return tuple of boolean and value)
            """
            if key not in fields:
                return False, None
            value = fields[key]
            if is_xblock:
                return value.is_set_on(fields_or_xblock), getattr(xblock, key)
            else:
                return True, value

        for key, criteria in qualifiers.iteritems():
            is_set, value = _is_set_on(key)
            if not is_set:
                return False
            if not self._value_matches(value, criteria):
                return False
        return True

    def _value_matches(self, target, criteria):
        ''' helper for _block_matches '''
        if isinstance(target, list):
            return any(self._value_matches(ele, criteria) for ele in target)
        elif isinstance(criteria, re._pattern_type):
            return criteria.search(target) is not None
        elif callable(criteria):
            return criteria(target)
        else:
            return criteria == target

    @abstractmethod
    def get_courses(self):
        '''
        Returns a list containing the top level XModuleDescriptors of the courses
        in this modulestore.
        '''
        pass

    @abstractmethod
    def get_course(self, course_id, depth=None):
        '''
        Look for a specific course id.  Returns the course descriptor, or None if not found.
        '''
        pass

    @abstractmethod
    def has_course(self, course_id, ignore_case=False):
        '''
        Look for a specific course id.  Returns whether it exists.
        '''
        pass

    @abstractmethod
    def get_parent_locations(self, location):
        '''Find all locations that are the parents of this location in this
        course.  Needed for path_to_location().

        returns an iterable of things that can be passed to Location.
        '''
        pass

    @abstractmethod
    def get_orphans(self, course_key):
        """
        Get all of the xblocks in the given course which have no parents and are not of types which are
        usually orphaned. NOTE: may include xblocks which still have references via xblocks which don't
        use children to point to their dependents.
        """
        pass

    @abstractmethod
    def get_errored_courses(self):
        """
        Return a dictionary of course_dir -> [(msg, exception_str)], for each
        course_dir where course loading failed.
        """
        pass

    @abstractmethod
    def get_modulestore_type(self, course_id):
        """
        Returns a type which identifies which modulestore is servicing the given
        course_id. The return can be either "xml" (for XML based courses) or "mongo" for MongoDB backed courses
        """
        pass


class ModuleStoreWrite(ModuleStoreRead):
    """
    An abstract interface for a database backend that stores XModuleDescriptor
    instances and extends both read and write functionality
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def update_item(self, xblock, user_id=None, allow_not_found=False, force=False):
        """
        Update the given xblock's persisted repr. Pass the user's unique id which the persistent store
        should save with the update if it has that ability.

        :param allow_not_found: whether this method should raise an exception if the given xblock
        has not been persisted before.
        :param force: fork the structure and don't update the course draftVersion if there's a version
        conflict (only applicable to version tracking and conflict detecting persistence stores)

        :raises VersionConflictError: if org, offering,  and version_guid given and the current
        version head != version_guid and force is not True. (only applicable to version tracking stores)
        """
        pass

    @abstractmethod
    def delete_item(self, location, user_id=None, **kwargs):
        """
        Delete an item from persistence. Pass the user's unique id which the persistent store
        should save with the update if it has that ability.

        :param delete_all_versions: removes both the draft and published version of this item from
        the course if using draft and old mongo. Split may or may not implement this.
        :param force: fork the structure and don't update the course draftVersion if there's a version
        conflict (only applicable to version tracking and conflict detecting persistence stores)

        :raises VersionConflictError: if org, offering,  and version_guid given and the current
        version head != version_guid and force is not True. (only applicable to version tracking stores)
        """
        pass

    @abstractmethod
    def create_course(self, org, offering, user_id=None, fields=None, **kwargs):
        """
        Creates and returns the course.

        Args:
            org (str): the organization that owns the course
            offering (str): the name of the course offering
            user_id: id of the user creating the course
            fields (dict): Fields to set on the course at initialization
            kwargs: Any optional arguments understood by a subset of modulestores to customize instantiation

        Returns: a CourseDescriptor
        """
        pass

    @abstractmethod
    def delete_course(self, course_key, user_id=None):
        """
        Deletes the course. It may be a soft or hard delete. It may or may not remove the xblock definitions
        depending on the persistence layer and how tightly bound the xblocks are to the course.

        Args:
            course_key (CourseKey): which course to delete
            user_id: id of the user creating the course
        """
        pass


class ModuleStoreReadBase(ModuleStoreRead):
    '''
    Implement interface functionality that can be shared.
    '''
    # pylint: disable=W0613

    def __init__(
        self,
        doc_store_config=None,  # ignore if passed up
        metadata_inheritance_cache_subsystem=None, request_cache=None,
        xblock_mixins=(), xblock_select=None,
        # temporary parms to enable backward compatibility. remove once all envs migrated
        db=None, collection=None, host=None, port=None, tz_aware=True, user=None, password=None,
        # allow lower level init args to pass harmlessly
        ** kwargs
    ):
        '''
        Set up the error-tracking logic.
        '''
        self._course_errors = defaultdict(make_error_tracker)  # location -> ErrorLog
        self.metadata_inheritance_cache_subsystem = metadata_inheritance_cache_subsystem
        self.request_cache = request_cache
        self.xblock_mixins = xblock_mixins
        self.xblock_select = xblock_select

    def get_course_errors(self, course_id):
        """
        Return list of errors for this :class:`.CourseKey`, if any.  Raise the same
        errors as get_item if course_id isn't present.
        """
        # check that item is present and raise the promised exceptions if needed
        # TODO (vshnayder): post-launch, make errors properties of items
        # self.get_item(location)
        assert(isinstance(course_id, CourseKey))
        return self._course_errors[course_id].errors

    def get_errored_courses(self):
        """
        Returns an empty dict.

        It is up to subclasses to extend this method if the concept
        of errored courses makes sense for their implementation.
        """
        return {}

    def get_course(self, course_id, depth=None):
        """Default impl--linear search through course list"""
        assert(isinstance(course_id, CourseKey))
        for c in self.get_courses():
            if c.id == course_id:
                return c
        return None

    def has_course(self, course_id, ignore_case=False):
        """Default impl--linear search through course list"""
        assert(isinstance(course_id, CourseKey))
        if ignore_case:
            return any(
                (c.id.org.lower() == course_id.org.lower() and c.id.offering.lower() == course_id.offering.lower())
                for c in self.get_courses()
            )
        else:
            return any(c.id == course_id for c in self.get_courses())

    def update_item(self, xblock, user_id=None, allow_not_found=False, force=False):
        """
        Update the given xblock's persisted repr. Pass the user's unique id which the persistent store
        should save with the update if it has that ability.

        :param allow_not_found: whether this method should raise an exception if the given xblock
        has not been persisted before.
        :param force: fork the structure and don't update the course draftVersion if there's a version
        conflict (only applicable to version tracking and conflict detecting persistence stores)

        :raises VersionConflictError: if org, offering,  and version_guid given and the current
        version head != version_guid and force is not True. (only applicable to version tracking stores)
        """
        raise NotImplementedError

    def delete_item(self, location, user_id=None, delete_all_versions=False, delete_children=False, force=False):
        """
        Delete an item from persistence. Pass the user's unique id which the persistent store
        should save with the update if it has that ability.

        :param delete_all_versions: removes both the draft and published version of this item from
        the course if using draft and old mongo. Split may or may not implement this.
        :param force: fork the structure and don't update the course draftVersion if there's a version
        conflict (only applicable to version tracking and conflict detecting persistence stores)

        :raises VersionConflictError: if org, offering,  and version_guid given and the current
        version head != version_guid and force is not True. (only applicable to version tracking stores)
        """
        raise NotImplementedError


class ModuleStoreWriteBase(ModuleStoreReadBase, ModuleStoreWrite):
    '''
    Implement interface functionality that can be shared.
    '''
    def __init__(self, **kwargs):
        super(ModuleStoreWriteBase, self).__init__(**kwargs)
        # TODO: Don't have a runtime just to generate the appropriate mixin classes (cpennington)
        # This is only used by partition_fields_by_scope, which is only needed because
        # the split mongo store is used for item creation as well as item persistence
        self.mixologist = Mixologist(self.xblock_mixins)

    def partition_fields_by_scope(self, category, fields):
        """
        Return dictionary of {scope: {field1: val, ..}..} for the fields of this potential xblock

        :param category: the xblock category
        :param fields: the dictionary of {fieldname: value}
        """
        if fields is None:
            return {}
        cls = self.mixologist.mix(XBlock.load_class(category, select=prefer_xmodules))
        result = collections.defaultdict(dict)
        for field_name, value in fields.iteritems():
            field = getattr(cls, field_name)
            result[field.scope][field_name] = value
        return result


def only_xmodules(identifier, entry_points):
    """Only use entry_points that are supplied by the xmodule package"""
    from_xmodule = [entry_point for entry_point in entry_points if entry_point.dist.key == 'xmodule']

    return default_select(identifier, from_xmodule)


def prefer_xmodules(identifier, entry_points):
    """Prefer entry_points from the xmodule package"""
    from_xmodule = [entry_point for entry_point in entry_points if entry_point.dist.key == 'xmodule']
    if from_xmodule:
        return default_select(identifier, from_xmodule)
    else:
        return default_select(identifier, entry_points)
