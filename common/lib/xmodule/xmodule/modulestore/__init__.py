"""
This module provides an abstraction for working with XModuleDescriptors
that are stored in a database an accessible using their Location as an identifier
"""

import logging
import re
import json
import datetime
from uuid import uuid4

from collections import namedtuple, defaultdict
import collections
from contextlib import contextmanager
import functools
import threading

from abc import ABCMeta, abstractmethod
from contracts import contract, new_contract
from xblock.plugin import default_select

from .exceptions import InvalidLocationError, InsufficientSpecificationError
from xmodule.errortracker import make_error_tracker
from xmodule.assetstore import AssetMetadata, AssetThumbnailMetadata
from opaque_keys.edx.keys import CourseKey, UsageKey, AssetKey
from opaque_keys.edx.locations import Location  # For import backwards compatibility
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xblock.runtime import Mixologist
from xblock.core import XBlock

log = logging.getLogger('edx.modulestore')

new_contract('CourseKey', CourseKey)
new_contract('AssetKey', AssetKey)
new_contract('AssetMetadata', AssetMetadata)
new_contract('AssetThumbnailMetadata', AssetThumbnailMetadata)


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


class BulkOpsRecord(object):
    """
    For handling nesting of bulk operations
    """
    def __init__(self):
        self._active_count = 0

    @property
    def active(self):
        """
        Return whether this bulk write is active.
        """
        return self._active_count > 0

    def nest(self):
        """
        Record another level of nesting of this bulk write operation
        """
        self._active_count += 1

    def unnest(self):
        """
        Record the completion of a level of nesting of the bulk write operation
        """
        self._active_count -= 1

    @property
    def is_root(self):
        """
        Return whether the bulk write is at the root (first) level of nesting
        """
        return self._active_count == 1


class ActiveBulkThread(threading.local):
    """
    Add the expected vars to the thread.
    """
    def __init__(self, bulk_ops_record_type, **kwargs):
        super(ActiveBulkThread, self).__init__(**kwargs)
        self.records = defaultdict(bulk_ops_record_type)


class BulkOperationsMixin(object):
    """
    This implements the :meth:`bulk_operations` modulestore semantics which handles nested invocations

    In particular, it implements :meth:`_begin_bulk_operation` and
    :meth:`_end_bulk_operation` to provide the external interface

    Internally, this mixin records the set of all active bulk operations (keyed on the active course),
    and only writes those values when :meth:`_end_bulk_operation` is called.
    If a bulk write operation isn't active, then the changes are immediately written to the underlying
    mongo_connection.
    """
    def __init__(self, *args, **kwargs):
        super(BulkOperationsMixin, self).__init__(*args, **kwargs)
        self._active_bulk_ops = ActiveBulkThread(self._bulk_ops_record_type)

    @contextmanager
    def bulk_operations(self, course_id):
        """
        A context manager for notifying the store of bulk operations. This affects only the current thread.

        In the case of Mongo, it temporarily disables refreshing the metadata inheritance tree
        until the bulk operation is completed.
        """
        try:
            self._begin_bulk_operation(course_id)
            yield
        finally:
            self._end_bulk_operation(course_id)

    # the relevant type of bulk_ops_record for the mixin (overriding classes should override
    # this variable)
    _bulk_ops_record_type = BulkOpsRecord

    def _get_bulk_ops_record(self, course_key, ignore_case=False):
        """
        Return the :class:`.BulkOpsRecord` for this course.
        """
        if course_key is None:
            return self._bulk_ops_record_type()

        # Retrieve the bulk record based on matching org/course/run (possibly ignoring case)
        if ignore_case:
            for key, record in self._active_bulk_ops.records.iteritems():
                if (
                    key.org.lower() == course_key.org.lower() and
                    key.course.lower() == course_key.course.lower() and
                    key.run.lower() == course_key.run.lower()
                ):
                    return record
        return self._active_bulk_ops.records[course_key.for_branch(None)]

    @property
    def _active_records(self):
        """
        Yield all active (CourseLocator, BulkOpsRecord) tuples.
        """
        for course_key, record in self._active_bulk_ops.records.iteritems():
            if record.active:
                yield (course_key, record)

    def _clear_bulk_ops_record(self, course_key):
        """
        Clear the record for this course
        """
        del self._active_bulk_ops.records[course_key.for_branch(None)]

    def _start_outermost_bulk_operation(self, bulk_ops_record, course_key):
        """
        The outermost nested bulk_operation call: do the actual begin of the bulk operation.

        Implementing classes must override this method; otherwise, the bulk operations are a noop
        """
        pass

    def _begin_bulk_operation(self, course_key):
        """
        Begin a bulk operation on course_key.
        """
        bulk_ops_record = self._get_bulk_ops_record(course_key)

        # Increment the number of active bulk operations (bulk operations
        # on the same course can be nested)
        bulk_ops_record.nest()

        # If this is the highest level bulk operation, then initialize it
        if bulk_ops_record.is_root:
            self._start_outermost_bulk_operation(bulk_ops_record, course_key)

    def _end_outermost_bulk_operation(self, bulk_ops_record, course_key):
        """
        The outermost nested bulk_operation call: do the actual end of the bulk operation.

        Implementing classes must override this method; otherwise, the bulk operations are a noop
        """
        pass

    def _end_bulk_operation(self, course_key):
        """
        End the active bulk operation on course_key.
        """
        # If no bulk op is active, return
        bulk_ops_record = self._get_bulk_ops_record(course_key)
        if not bulk_ops_record.active:
            return

        bulk_ops_record.unnest()

        # If this wasn't the outermost context, then don't close out the
        # bulk operation.
        if bulk_ops_record.active:
            return

        self._end_outermost_bulk_operation(bulk_ops_record, course_key)

        self._clear_bulk_ops_record(course_key)

    def _is_in_bulk_operation(self, course_key, ignore_case=False):
        """
        Return whether a bulk operation is active on `course_key`.
        """
        return self._get_bulk_ops_record(course_key, ignore_case).active


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
    def get_item(self, usage_key, depth=0, **kwargs):
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
    def get_items(self, location, course_id=None, depth=0, qualifiers=None, **kwargs):
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
    def make_course_key(self, org, course, run):
        """
        Return a valid :class:`~opaque_keys.edx.keys.CourseKey` for this modulestore
        that matches the supplied `org`, `course`, and `run`.

        This key may represent a course that doesn't exist in this modulestore.
        """
        pass

    @abstractmethod
    def get_courses(self, **kwargs):
        '''
        Returns a list containing the top level XModuleDescriptors of the courses
        in this modulestore.
        '''
        pass

    @abstractmethod
    def get_course(self, course_id, depth=0, **kwargs):
        '''
        Look for a specific course by its id (:class:`CourseKey`).
        Returns the course descriptor, or None if not found.
        '''
        pass

    @abstractmethod
    def has_course(self, course_id, ignore_case=False, **kwargs):
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
        '''
        Find the location that is the parent of this location in this
        course.  Needed for path_to_location().
        '''
        pass

    @abstractmethod
    def get_orphans(self, course_key, **kwargs):
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
    def get_courses_for_wiki(self, wiki_slug, **kwargs):
        """
        Return the list of courses which use this wiki_slug
        :param wiki_slug: the course wiki root slug
        :return: list of course keys
        """
        pass

    @abstractmethod
    def has_published_version(self, xblock):
        """
        Returns true if this xblock exists in the published course regardless of whether it's up to date
        """
        pass

    @abstractmethod
    def close_connections(self):
        """
        Closes any open connections to the underlying databases
        """
        pass

    @contextmanager
    def bulk_operations(self, course_id):
        """
        A context manager for notifying the store of bulk operations. This affects only the current thread.
        """
        yield

    def ensure_indexes(self):
        """
        Ensure that all appropriate indexes are created that are needed by this modulestore, or raise
        an exception if unable to.

        This method is intended for use by tests and administrative commands, and not
        to be run during server startup.
        """
        pass


class ModuleStoreWrite(ModuleStoreRead):
    """
    An abstract interface for a database backend that stores XModuleDescriptor
    instances and extends both read and write functionality
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def update_item(self, xblock, user_id, allow_not_found=False, force=False, **kwargs):
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
    def create_item(self, user_id, course_key, block_type, block_id=None, fields=None, **kwargs):
        """
        Creates and saves a new item in a course.

        Returns the newly created item.

        Args:
            user_id: ID of the user creating and saving the xmodule
            course_key: A :class:`~opaque_keys.edx.CourseKey` identifying which course to create
                this item in
            block_type: The type of block to create
            block_id: a unique identifier for the new item. If not supplied,
                a new identifier will be generated
            fields (dict): A dictionary specifying initial values for some or all fields
                in the newly created block
        """
        pass

    @abstractmethod
    def clone_course(self, source_course_id, dest_course_id, user_id, fields=None):
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
    def delete_course(self, course_key, user_id, **kwargs):
        """
        Deletes the course. It may be a soft or hard delete. It may or may not remove the xblock definitions
        depending on the persistence layer and how tightly bound the xblocks are to the course.

        Args:
            course_key (CourseKey): which course to delete
            user_id: id of the user deleting the course
        """
        pass

    @abstractmethod
    def _drop_database(self):
        """
        A destructive operation to drop the underlying database and close all connections.
        Intended to be used by test code for cleanup.
        """
        pass


class ModuleStoreReadBase(BulkOperationsMixin, ModuleStoreRead):
    '''
    Implement interface functionality that can be shared.
    '''
    # pylint: disable=W0613

    def __init__(
        self,
        contentstore=None,
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
        super(ModuleStoreReadBase, self).__init__(**kwargs)
        self._course_errors = defaultdict(make_error_tracker)  # location -> ErrorLog
        # TODO move the inheritance_cache_subsystem to classes which use it
        self.metadata_inheritance_cache_subsystem = metadata_inheritance_cache_subsystem
        self.request_cache = request_cache
        self.xblock_mixins = xblock_mixins
        self.xblock_select = xblock_select
        self.contentstore = contentstore

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

    def get_course(self, course_id, depth=0, **kwargs):
        """
        See ModuleStoreRead.get_course

        Default impl--linear search through course list
        """
        assert(isinstance(course_id, CourseKey))
        for course in self.get_courses(**kwargs):
            if course.id == course_id:
                return course
        return None

    def has_course(self, course_id, ignore_case=False, **kwargs):
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
                    if c.id.org.lower() == course_id.org.lower() and
                    c.id.course.lower() == course_id.course.lower() and
                    c.id.run.lower() == course_id.run.lower()
                ),
                None
            )
        else:
            return next(
                (c.id for c in self.get_courses() if c.id == course_id),
                None
            )

    def has_published_version(self, xblock):
        """
        Returns True since this is a read-only store.
        """
        return True

    def heartbeat(self):
        """
        Is this modulestore ready?
        """
        # default is to say yes by not raising an exception
        return {'default_impl': True}

    def close_connections(self):
        """
        Closes any open connections to the underlying databases
        """
        if self.contentstore:
            self.contentstore.close_connections()
        super(ModuleStoreReadBase, self).close_connections()

    @contextmanager
    def default_store(self, store_type):
        """
        A context manager for temporarily changing the default store
        """
        if self.get_modulestore_type(None) != store_type:
            raise ValueError(u"Cannot set default store to type {}".format(store_type))
        yield

    @staticmethod
    def memoize_request_cache(func):
        """
        Memoize a function call results on the request_cache if there's one. Creates the cache key by
        joining the unicode of all the args with &; so, if your arg may use the default &, it may
        have false hits
        """
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            """
            Wraps a method to memoize results.
            """
            if self.request_cache:
                cache_key = '&'.join([hashvalue(arg) for arg in args])
                if cache_key in self.request_cache.data.setdefault(func.__name__, {}):
                    return self.request_cache.data[func.__name__][cache_key]

                result = func(self, *args, **kwargs)

                self.request_cache.data[func.__name__][cache_key] = result
                return result
            else:
                return func(self, *args, **kwargs)
        return wrapper


def hashvalue(arg):
    """
    If arg is an xblock, use its location. otherwise just turn it into a string
    """
    if isinstance(arg, XBlock):
        return unicode(arg.location)
    else:
        return unicode(arg)


class ModuleStoreWriteBase(ModuleStoreReadBase, ModuleStoreWrite):
    '''
    Implement interface functionality that can be shared.
    '''
    def __init__(self, contentstore, **kwargs):
        super(ModuleStoreWriteBase, self).__init__(contentstore=contentstore, **kwargs)

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
        result = collections.defaultdict(dict)
        if fields is None:
            return result
        cls = self.mixologist.mix(XBlock.load_class(category, select=prefer_xmodules))
        for field_name, value in fields.iteritems():
            field = getattr(cls, field_name)
            result[field.scope][field_name] = value
        return result

    def create_course(self, org, course, run, user_id, fields=None, runtime=None, **kwargs):
        """
        Creates any necessary other things for the course as a side effect and doesn't return
        anything useful. The real subclass should call this before it returns the course.
        """
        # clone a default 'about' overview module as well
        about_location = self.make_course_key(org, course, run).make_usage_key('about', 'overview')

        about_descriptor = XBlock.load_class('about')
        overview_template = about_descriptor.get_template('overview.yaml')
        self.create_item(
            user_id,
            about_location.course_key,
            about_location.block_type,
            block_id=about_location.block_id,
            definition_data={'data': overview_template.get('data')},
            metadata=overview_template.get('metadata'),
            runtime=runtime,
            continue_version=True,
        )

    def clone_course(self, source_course_id, dest_course_id, user_id, fields=None, **kwargs):
        """
        This base method just copies the assets. The lower level impls must do the actual cloning of
        content.
        """
        # copy the assets
        if self.contentstore:
            self.contentstore.copy_all_course_assets(source_course_id, dest_course_id)
        return dest_course_id

    def delete_course(self, course_key, user_id, **kwargs):
        """
        This base method just deletes the assets. The lower level impls must do the actual deleting of
        content.
        """
        # delete the assets
        if self.contentstore:
            self.contentstore.delete_all_course_assets(course_key)
        super(ModuleStoreWriteBase, self).delete_course(course_key, user_id)

    def _drop_database(self):
        """
        A destructive operation to drop the underlying database and close all connections.
        Intended to be used by test code for cleanup.
        """
        if self.contentstore:
            self.contentstore._drop_database()  # pylint: disable=protected-access
        super(ModuleStoreWriteBase, self)._drop_database()  # pylint: disable=protected-access

    def create_child(self, user_id, parent_usage_key, block_type, block_id=None, fields=None, **kwargs):
        """
        Creates and saves a new xblock that as a child of the specified block

        Returns the newly created item.

        Args:
            user_id: ID of the user creating and saving the xmodule
            parent_usage_key: a :class:`~opaque_key.edx.UsageKey` identifing the
                block that this item should be parented under
            block_type: The type of block to create
            block_id: a unique identifier for the new item. If not supplied,
                a new identifier will be generated
            fields (dict): A dictionary specifying initial values for some or all fields
                in the newly created block
        """
        item = self.create_item(user_id, parent_usage_key.course_key, block_type, block_id=block_id, fields=fields, **kwargs)
        parent = self.get_item(parent_usage_key)
        parent.children.append(item.location)
        self.update_item(parent, user_id)

    def _find_course_assets(self, course_key):
        """
        Base method to override.
        """
        raise NotImplementedError()

    def _find_course_asset(self, course_key, filename, get_thumbnail=False):
        """
        Internal; finds or creates course asset info -and- finds existing asset (or thumbnail) metadata.

        Arguments:
            course_key (CourseKey): course identifier
            filename (str): filename of the asset or thumbnail
            get_thumbnail (bool): True gets thumbnail data, False gets asset data

        Returns:
            Asset info for the course, index of asset/thumbnail in list (None if asset/thumbnail does not exist)
        """
        course_assets = self._find_course_assets(course_key)

        if get_thumbnail:
            all_assets = course_assets['thumbnails']
        else:
            all_assets = course_assets['assets']

        # See if this asset already exists by checking the external_filename.
        # Studio doesn't currently support using multiple course assets with the same filename.
        # So use the filename as the unique identifier.
        for idx, asset in enumerate(all_assets):
            if asset['filename'] == filename:
                return course_assets, idx

        return course_assets, None

    def _save_asset_info(self, course_key, asset_metadata, user_id, thumbnail=False):
        """
        Base method to over-ride in modulestore.
        """
        raise NotImplementedError()

    @contract(course_key='CourseKey', asset_metadata='AssetMetadata')
    def save_asset_metadata(self, course_key, asset_metadata, user_id):
        """
        Saves the asset metadata for a particular course's asset.

        Arguments:
            course_key (CourseKey): course identifier
            asset_metadata (AssetMetadata): data about the course asset data

        Returns:
            True if metadata save was successful, else False
        """
        return self._save_asset_info(course_key, asset_metadata, user_id, thumbnail=False)

    @contract(course_key='CourseKey', asset_thumbnail_metadata='AssetThumbnailMetadata')
    def save_asset_thumbnail_metadata(self, course_key, asset_thumbnail_metadata, user_id):
        """
        Saves the asset thumbnail metadata for a particular course asset's thumbnail.

        Arguments:
            course_key (CourseKey): course identifier
            asset_thumbnail_metadata (AssetThumbnailMetadata): data about the course asset thumbnail

        Returns:
            True if thumbnail metadata save was successful, else False
        """
        return self._save_asset_info(course_key, asset_thumbnail_metadata, user_id, thumbnail=True)

    @contract(asset_key='AssetKey')
    def _find_asset_info(self, asset_key, thumbnail=False, **kwargs):
        """
        Find the info for a particular course asset/thumbnail.

        Arguments:
            asset_key (AssetKey): key containing original asset filename
            thumbnail (bool): True if finding thumbnail, False if finding asset metadata

        Returns:
            asset/thumbnail metadata (AssetMetadata/AssetThumbnailMetadata) -or- None if not found
        """
        course_assets, asset_idx = self._find_course_asset(asset_key.course_key, asset_key.path, thumbnail)
        if asset_idx is None:
            return None

        if thumbnail:
            info = 'thumbnails'
            mdata = AssetThumbnailMetadata(asset_key, asset_key.path, **kwargs)
        else:
            info = 'assets'
            mdata = AssetMetadata(asset_key, asset_key.path, **kwargs)
        all_assets = course_assets[info]
        mdata.from_mongo(all_assets[asset_idx])
        return mdata

    @contract(asset_key='AssetKey')
    def find_asset_metadata(self, asset_key, **kwargs):
        """
        Find the metadata for a particular course asset.

        Arguments:
            asset_key (AssetKey): key containing original asset filename

        Returns:
            asset metadata (AssetMetadata) -or- None if not found
        """
        return self._find_asset_info(asset_key, thumbnail=False, **kwargs)

    @contract(asset_key='AssetKey')
    def find_asset_thumbnail_metadata(self, asset_key, **kwargs):
        """
        Find the metadata for a particular course asset.

        Arguments:
            asset_key (AssetKey): key containing original asset filename

        Returns:
            asset metadata (AssetMetadata) -or- None if not found
        """
        return self._find_asset_info(asset_key, thumbnail=True, **kwargs)

    @contract(course_key='CourseKey', start='int | None', maxresults='int | None', sort='list | None', get_thumbnails='bool')
    def _get_all_asset_metadata(self, course_key, start=0, maxresults=-1, sort=None, get_thumbnails=False, **kwargs):
        """
        Returns a list of static asset (or thumbnail) metadata for a course.

        Args:
            course_key (CourseKey): course identifier
            start (int): optional - start at this asset number
            maxresults (int): optional - return at most this many, -1 means no limit
            sort (array): optional - None means no sort
                (sort_by (str), sort_order (str))
                sort_by - one of 'uploadDate' or 'displayname'
                sort_order - one of 'ascending' or 'descending'
            get_thumbnails (bool): True if getting thumbnail metadata, else getting asset metadata

        Returns:
            List of AssetMetadata or AssetThumbnailMetadata objects.
        """
        course_assets = self._find_course_assets(course_key)
        if course_assets is None:
            # If no course assets are found, return None instead of empty list
            # to distinguish zero assets from "not able to retrieve assets".
            return None

        if get_thumbnails:
            all_assets = course_assets.get('thumbnails', [])
        else:
            all_assets = course_assets.get('assets', [])

        # DO_NEXT: Add start/maxresults/sort functionality as part of https://openedx.atlassian.net/browse/PLAT-74
        if start and maxresults and sort:
            pass

        ret_assets = []
        for asset in all_assets:
            if get_thumbnails:
                thumb = AssetThumbnailMetadata(
                    course_key.make_asset_key('thumbnail', asset['filename']),
                    internal_name=asset['filename'], **kwargs
                )
                ret_assets.append(thumb)
            else:
                asset = AssetMetadata(
                    course_key.make_asset_key('asset', asset['filename']),
                    basename=asset['filename'],
                    edited_on=asset['edit_info']['edited_on'],
                    contenttype=asset['contenttype'],
                    md5=str(asset['md5']), **kwargs
                )
                ret_assets.append(asset)
        return ret_assets

    @contract(course_key='CourseKey', start='int | None', maxresults='int | None', sort='list | None')
    def get_all_asset_metadata(self, course_key, start=0, maxresults=-1, sort=None, **kwargs):
        """
        Returns a list of static assets for a course.
        By default all assets are returned, but start and maxresults can be provided to limit the query.

        Args:
            course_key (CourseKey): course identifier
            start (int): optional - start at this asset number
            maxresults (int): optional - return at most this many, -1 means no limit
            sort (array): optional - None means no sort
                (sort_by (str), sort_order (str))
                sort_by - one of 'uploadDate' or 'displayname'
                sort_order - one of 'ascending' or 'descending'

        Returns:
            List of AssetMetadata objects.
        """
        return self._get_all_asset_metadata(course_key, start, maxresults, sort, get_thumbnails=False, **kwargs)

    @contract(course_key='CourseKey')
    def get_all_asset_thumbnail_metadata(self, course_key, **kwargs):
        """
        Returns a list of thumbnails for all course assets.

        Args:
            course_key (CourseKey): course identifier

        Returns:
            List of AssetThumbnailMetadata objects.
        """
        return self._get_all_asset_metadata(course_key, get_thumbnails=True, **kwargs)

    def set_asset_metadata_attrs(self, asset_key, attrs, user_id):
        """
        Base method to over-ride in modulestore.
        """
        raise NotImplementedError()

    def _delete_asset_data(self, asset_key, user_id, thumbnail=False):
        """
        Base method to over-ride in modulestore.
        """
        raise NotImplementedError()

    @contract(asset_key='AssetKey', attr=str)
    def set_asset_metadata_attr(self, asset_key, attr, value, user_id):
        """
        Add/set the given attr on the asset at the given location. Value can be any type which pymongo accepts.

        Arguments:
            asset_key (AssetKey): asset identifier
            attr (str): which attribute to set
            value: the value to set it to (any type pymongo accepts such as datetime, number, string)

        Raises:
            ItemNotFoundError if no such item exists
            AttributeError is attr is one of the build in attrs.
        """
        return self.set_asset_metadata_attrs(asset_key, {attr: value}, user_id)

    @contract(asset_key='AssetKey')
    def delete_asset_metadata(self, asset_key, user_id):
        """
        Deletes a single asset's metadata.

        Arguments:
            asset_key (AssetKey): locator containing original asset filename

        Returns:
            Number of asset metadata entries deleted (0 or 1)
        """
        return self._delete_asset_data(asset_key, user_id, thumbnail=False)

    @contract(asset_key='AssetKey')
    def delete_asset_thumbnail_metadata(self, asset_key, user_id):
        """
        Deletes a single asset's metadata.

        Arguments:
            asset_key (AssetKey): locator containing original asset filename

        Returns:
            Number of asset metadata entries deleted (0 or 1)
        """
        return self._delete_asset_data(asset_key, user_id, thumbnail=True)

    @contract(source_course_key='CourseKey', dest_course_key='CourseKey')
    def copy_all_asset_metadata(self, source_course_key, dest_course_key, user_id):
        """
        Copy all the course assets from source_course_key to dest_course_key.

        Arguments:
            source_course_key (CourseKey): identifier of course to copy from
            dest_course_key (CourseKey): identifier of course to copy to
        """
        pass


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
        if isinstance(obj, (CourseKey, UsageKey)):
            return unicode(obj)
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
