"""
This module provides an abstraction for working with XModuleDescriptors
that are stored in a database an accessible using their Location as an identifier
"""

import logging
import re
import json
import datetime

from collections import namedtuple, defaultdict
import collections
from contextlib import contextmanager

from abc import ABCMeta, abstractmethod
from xblock.plugin import default_select

from .exceptions import InvalidLocationError, InsufficientSpecificationError
from xmodule.errortracker import make_error_tracker
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locations import Location  # For import backwards compatibility
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xblock.runtime import Mixologist
from xblock.core import XBlock

log = logging.getLogger('edx.modulestore')


class ModuleStoreEnum(object):
    """
    A class to encapsulate common constants that are used with the various modulestores.
    """

    class Type(object):
        """
        The various types of modulestores provided
        """
        split = 'split'
        mongo = 'mongo'
        xml = 'xml'

    class RevisionOption(object):
        """
        Revision constants to use for Module Store operations
        Note: These values are passed into store APIs and only used at run time
        """
        # both DRAFT and PUBLISHED versions are queried, with preference to DRAFT versions
        draft_preferred = 'rev-opt-draft-preferred'

        # only DRAFT versions are queried and no PUBLISHED versions
        draft_only = 'rev-opt-draft-only'

        # # only PUBLISHED versions are queried and no DRAFT versions
        published_only = 'rev-opt-published-only'

        # all revisions are queried
        all = 'rev-opt-all'

    class Branch(object):
        """
        Branch constants to use for stores, such as Mongo, that have only 2 branches: DRAFT and PUBLISHED
        Note: These values are taken from server configuration settings, so should not be changed without alerting DevOps
        """
        draft_preferred = 'draft-preferred'
        published_only = 'published-only'

    class BranchName(object):
        """
        Branch constants to use for stores, such as Split, that have named branches
        """
        draft = 'draft-branch'
        published = 'published-branch'

    class UserID(object):
        """
        Values for user ID defaults
        """
        # Note: we use negative values here to (try to) not collide
        # with user identifiers provided by actual user services.

        # user ID to use for all management commands
        mgmt_command = -1

        # user ID to use for primitive commands
        primitive_command = -2

        # user ID to use for tests that do not have a django user available
        test = -3

class PublishState(object):
    """
    The publish state for a given xblock-- either 'draft', 'private', or 'public'.

    Currently in CMS, an xblock can only be in 'draft' or 'private' if it is at or below the Unit level.
    """
    draft = 'draft'
    private = 'private'
    public = 'public'


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
    def get_course_errors(self, course_key):
        """
        Return a list of (msg, exception-or-None) errors that the modulestore
        encountered when loading the course at course_id.

        Raises the same exceptions as get_item if the location isn't found or
        isn't fully specified.

        Args:
            course_key (:class:`.CourseKey`): The course to check for errors
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
            fields_or_xblock (dict or XBlock): either the json blob (from the db or get_explicitly_set_fields)
                or the xblock.fields() value or the XBlock from which to get those values
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
            Is this key set in fields? (return tuple of boolean and value). A helper which can
            handle fields either being the json doc or xblock fields. Is inner function to restrict
            use and to access local vars.
            """
            if key not in fields:
                return False, None
            field = fields[key]
            if is_xblock:
                return field.is_set_on(fields_or_xblock), getattr(xblock, key)
            else:
                return True, field

        for key, criteria in qualifiers.iteritems():
            is_set, value = _is_set_on(key)
            if not is_set:
                return False
            if not self._value_matches(value, criteria):
                return False
        return True

    def _value_matches(self, target, criteria):
        '''
        helper for _block_matches: does the target (field value) match the criteria?

        If target is a list, do any of the list elements meet the criteria
        If the criteria is a regex, does the target match it?
        If the criteria is a function, does invoking it on the target yield something truthy?
        Otherwise, is the target == criteria
        '''
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
    def get_course(self, course_id, depth=0):
        '''
        Look for a specific course by its id (:class:`CourseKey`).
        Returns the course descriptor, or None if not found.
        '''
        pass

    @abstractmethod
    def has_course(self, course_id, ignore_case=False):
        '''
        Look for a specific course id.  Returns whether it exists.
        Args:
            course_id (CourseKey):
            ignore_case (boolean): some modulestores are case-insensitive. Use this flag
                to search for whether a potentially conflicting course exists in that case.
        '''
        pass

    @abstractmethod
    def get_parent_location(self, location, **kwargs):
        '''Find the location that is the parent of this location in this
        course.  Needed for path_to_location().
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

    @abstractmethod
    def compute_publish_state(self, xblock):
        """
        Returns whether this xblock is draft, public, or private.

        Returns:
            PublishState.draft - content is in the process of being edited, but still has a previous
                version deployed to LMS
            PublishState.public - content is locked and deployed to LMS
            PublishState.private - content is editable and not deployed to LMS
        """
        pass

class ModuleStoreWrite(ModuleStoreRead):
    """
    An abstract interface for a database backend that stores XModuleDescriptor
    instances and extends both read and write functionality
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def update_item(self, xblock, user_id, allow_not_found=False, force=False):
        """
        Update the given xblock's persisted repr. Pass the user's unique id which the persistent store
        should save with the update if it has that ability.

        :param allow_not_found: whether this method should raise an exception if the given xblock
        has not been persisted before.
        :param force: fork the structure and don't update the course draftVersion if there's a version
        conflict (only applicable to version tracking and conflict detecting persistence stores)

        :raises VersionConflictError: if org, course, run, and version_guid given and the current
        version head != version_guid and force is not True. (only applicable to version tracking stores)
        """
        pass

    @abstractmethod
    def delete_item(self, location, user_id, **kwargs):
        """
        Delete an item and its subtree from persistence. Remove the item from any parents (Note, does not
        affect parents from other branches or logical branches; thus, in old mongo, deleting something
        whose parent cannot be draft, deletes it from both but deleting a component under a draft vertical
        only deletes it from the draft.

        Pass the user's unique id which the persistent store
        should save with the update if it has that ability.

        :param force: fork the structure and don't update the course draftVersion if there's a version
        conflict (only applicable to version tracking and conflict detecting persistence stores)

        :raises VersionConflictError: if org, course, run, and version_guid given and the current
        version head != version_guid and force is not True. (only applicable to version tracking stores)
        """
        pass

    @abstractmethod
    def create_course(self, org, course, run, user_id, fields=None, **kwargs):
        """
        Creates and returns the course.

        Args:
            org (str): the organization that owns the course
            course (str): the name of the course
            run (str): the name of the run
            user_id: id of the user creating the course
            fields (dict): Fields to set on the course at initialization
            kwargs: Any optional arguments understood by a subset of modulestores to customize instantiation

        Returns: a CourseDescriptor
        """
        pass

    @abstractmethod
    def clone_course(self, source_course_id, dest_course_id, user_id):
        """
        Sets up source_course_id to point a course with the same content as the desct_course_id. This
        operation may be cheap or expensive. It may have to copy all assets and all xblock content or
        merely setup new pointers.

        Backward compatibility: this method used to require in some modulestores that dest_course_id
        pointed to an empty but already created course. Implementers should support this or should
        enable creating the course from scratch.

        Raises:
            ItemNotFoundError: if the source course doesn't exist (or any of its xblocks aren't found)
            DuplicateItemError: if the destination course already exists (with content in some cases)
        """
        pass

    @abstractmethod
    def delete_course(self, course_key, user_id):
        """
        Deletes the course. It may be a soft or hard delete. It may or may not remove the xblock definitions
        depending on the persistence layer and how tightly bound the xblocks are to the course.

        Args:
            course_key (CourseKey): which course to delete
            user_id: id of the user deleting the course
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

    def get_course_errors(self, course_key):
        """
        Return list of errors for this :class:`.CourseKey`, if any.  Raise the same
        errors as get_item if course_key isn't present.
        """
        # check that item is present and raise the promised exceptions if needed
        # TODO (vshnayder): post-launch, make errors properties of items
        # self.get_item(location)
        assert(isinstance(course_key, CourseKey))
        return self._course_errors[course_key].errors

    def get_errored_courses(self):
        """
        Returns an empty dict.

        It is up to subclasses to extend this method if the concept
        of errored courses makes sense for their implementation.
        """
        return {}

    def get_course(self, course_id, depth=0):
        """
        See ModuleStoreRead.get_course

        Default impl--linear search through course list
        """
        assert(isinstance(course_id, CourseKey))
        for course in self.get_courses():
            if course.id == course_id:
                return course
        return None

    def has_course(self, course_id, ignore_case=False):
        """
        Returns the course_id of the course if it was found, else None
        Args:
            course_id (CourseKey):
            ignore_case (boolean): some modulestores are case-insensitive. Use this flag
                to search for whether a potentially conflicting course exists in that case.
        """
        # linear search through list
        assert(isinstance(course_id, CourseKey))
        if ignore_case:
            return next(
                (
                    c.id for c in self.get_courses()
                    if c.id.org.lower() == course_id.org.lower() and \
                    c.id.course.lower() == course_id.course.lower() and \
                    c.id.run.lower() == course_id.run.lower()
                ),
                None
            )
        else:
            return next(
                (c.id for c in self.get_courses() if c.id == course_id),
                None
            )

    def compute_publish_state(self, xblock):
        """
        Returns PublishState.public since this is a read-only store.
        """
        return PublishState.public

    def heartbeat(self):
        """
        Is this modulestore ready?
        """
        # default is to say yes by not raising an exception
        return {'default_impl': True}

    @contextmanager
    def default_store(self, store_type):
        """
        A context manager for temporarily changing the default store
        """
        if self.get_modulestore_type(None) != store_type:
            raise ValueError(u"Cannot set default store to type {}".format(store_type))
        yield

    @contextmanager
    def branch_setting(self, branch_setting, course_id=None):
        """
        A context manager for temporarily setting a store's branch value
        """
        previous_branch_setting_func = getattr(self, 'branch_setting_func', None)
        try:
            self.branch_setting_func = lambda: branch_setting
            yield
        finally:
            self.branch_setting_func = previous_branch_setting_func


class ModuleStoreWriteBase(ModuleStoreReadBase, ModuleStoreWrite):
    '''
    Implement interface functionality that can be shared.
    '''
    def __init__(self, contentstore, **kwargs):
        super(ModuleStoreWriteBase, self).__init__(**kwargs)

        self.contentstore = contentstore
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

    def update_item(self, xblock, user_id, allow_not_found=False, force=False):
        """
        Update the given xblock's persisted repr. Pass the user's unique id which the persistent store
        should save with the update if it has that ability.

        :param allow_not_found: whether this method should raise an exception if the given xblock
        has not been persisted before.
        :param force: fork the structure and don't update the course draftVersion if there's a version
        conflict (only applicable to version tracking and conflict detecting persistence stores)

        :raises VersionConflictError: if org, course, run, and version_guid given and the current
        version head != version_guid and force is not True. (only applicable to version tracking stores)
        """
        raise NotImplementedError

    def delete_item(self, location, user_id, force=False):
        """
        Delete an item from persistence. Pass the user's unique id which the persistent store
        should save with the update if it has that ability.

        :param user_id: ID of the user deleting the item
        :param force: fork the structure and don't update the course draftVersion if there's a version
        conflict (only applicable to version tracking and conflict detecting persistence stores)

        :raises VersionConflictError: if org, course, run, and version_guid given and the current
        version head != version_guid and force is not True. (only applicable to version tracking stores)
        """
        raise NotImplementedError

    def create_and_save_xmodule(self, location, user_id, definition_data=None, metadata=None, runtime=None, fields={}):
        """
        Create the new xmodule and save it.

        :param location: a Location--must have a category
        :param user_id: ID of the user creating and saving the xmodule
        :param definition_data: can be empty. The initial definition_data for the kvs
        :param metadata: can be empty, the initial metadata for the kvs
        :param runtime: if you already have an xblock from the course, the xblock.runtime value
        :param fields: a dictionary of field names and values for the new xmodule
        """
        new_object = self.create_xmodule(location, definition_data, metadata, runtime, fields)
        self.update_item(new_object, user_id, allow_not_found=True)
        return new_object

    def clone_course(self, source_course_id, dest_course_id, user_id):
        """
        This base method just copies the assets. The lower level impls must do the actual cloning of
        content.
        """
        # copy the assets
        self.contentstore.copy_all_course_assets(source_course_id, dest_course_id)
        super(ModuleStoreWriteBase, self).clone_course(source_course_id, dest_course_id, user_id)
        return dest_course_id

    def delete_course(self, course_key, user_id):
        """
        This base method just deletes the assets. The lower level impls must do the actual deleting of
        content.
        """
        # delete the assets
        self.contentstore.delete_all_course_assets(course_key)
        super(ModuleStoreWriteBase, self).delete_course(course_key, user_id)

    @contextmanager
    def bulk_write_operations(self, course_id):
        """
        A context manager for notifying the store of bulk write events.

        In the case of Mongo, it temporarily disables refreshing the metadata inheritance tree
        until the bulk operation is completed.
        """
        # TODO
        # Make this multi-process-safe if future operations need it.
        # Right now, only Import Course, Clone Course, and Delete Course use this, so
        # it's ok if the cached metadata in the memcache is invalid when another
        # request comes in for the same course.
        try:
            if hasattr(self, '_begin_bulk_write_operation'):
                self._begin_bulk_write_operation(course_id)
            yield
        finally:
            # check for the begin method here,
            # since it's an error if an end method is not defined when a begin method is
            if hasattr(self, '_begin_bulk_write_operation'):
                self._end_bulk_write_operation(course_id)


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


class EdxJSONEncoder(json.JSONEncoder):
    """
    Custom JSONEncoder that handles `Location` and `datetime.datetime` objects.

    `Location`s are encoded as their url string form, and `datetime`s as
    ISO date strings
    """
    def default(self, obj):
        if isinstance(obj, Location):
            return obj.to_deprecated_string()
        elif isinstance(obj, datetime.datetime):
            if obj.tzinfo is not None:
                if obj.utcoffset() is None:
                    return obj.isoformat() + 'Z'
                else:
                    return obj.isoformat()
            else:
                return obj.isoformat()
        else:
            return super(EdxJSONEncoder, self).default(obj)
