"""
MixedModuleStore allows for aggregation between multiple modulestores.

In this way, courses can be served up both - say - XMLModuleStore or MongoModuleStore

"""

import logging
from contextlib import contextmanager
from opaque_keys import InvalidKeyError

from . import ModuleStoreWriteBase
from xmodule.modulestore import ModuleStoreEnum, compute_location_from_args
from xmodule.modulestore.django import create_modulestore_instance
from xmodule.modulestore.exceptions import ItemNotFoundError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
import itertools
from xmodule.modulestore.split_migrator import SplitMigrator


log = logging.getLogger(__name__)


class MixedModuleStore(ModuleStoreWriteBase):
    """
    ModuleStore knows how to route requests to the right persistence ms
    """
    def __init__(self, contentstore, mappings, stores, i18n_service=None, **kwargs):
        """
        Initialize a MixedModuleStore. Here we look into our passed in kwargs which should be a
        collection of other modulestore configuration information
        """
        super(MixedModuleStore, self).__init__(contentstore, **kwargs)

        self.modulestores = []
        self.mappings = {}

        for course_id, store_name in mappings.iteritems():
            try:
                self.mappings[CourseKey.from_string(course_id)] = store_name
            except InvalidKeyError:
                try:
                    self.mappings[SlashSeparatedCourseKey.from_deprecated_string(course_id)] = store_name
                except InvalidKeyError:
                    log.exception("Invalid MixedModuleStore configuration. Unable to parse course_id %r", course_id)
                    continue

        for store_settings in stores:
            key = store_settings['NAME']
            is_xml = 'XMLModuleStore' in store_settings['ENGINE']
            if is_xml:
                # restrict xml to only load courses in mapping
                store_settings['OPTIONS']['course_ids'] = [
                    course_key.to_deprecated_string()
                    for course_key, store_key in self.mappings.iteritems()
                    if store_key == key
                ]
            store = create_modulestore_instance(
                store_settings['ENGINE'],
                self.contentstore,
                store_settings.get('DOC_STORE_CONFIG', {}),
                store_settings.get('OPTIONS', {}),
                i18n_service=i18n_service,
            )
            # replace all named pointers to the store into actual pointers
            for course_key, store_name in self.mappings.iteritems():
                if store_name == key:
                    self.mappings[course_key] = store
            self.modulestores.append(store)

    def _clean_course_id_for_mapping(self, course_id):
        """
        In order for mapping to work, the course_id must be minimal--no version, no branch--
        as we never store one version or one branch in one ms and another in another ms.

        :param course_id: the CourseKey
        """
        if hasattr(course_id, 'version_agnostic'):
            course_id = course_id.version_agnostic()
        if hasattr(course_id, 'branch'):
            course_id = course_id.replace(branch=None)
        return course_id

    def _get_modulestore_for_courseid(self, course_id=None):
        """
        For a given course_id, look in the mapping table and see if it has been pinned
        to a particular modulestore

        If course_id is None, returns the first (ordered) store as the default
        """
        if course_id is not None:
            course_id = self._clean_course_id_for_mapping(course_id)
            mapping = self.mappings.get(course_id, None)
            if mapping is not None:
                return mapping
            else:
                for store in self.modulestores:
                    if isinstance(course_id, store.reference_type) and store.has_course(course_id):
                        self.mappings[course_id] = store
                        return store

        # return the first store, as the default
        return self.modulestores[0]

    def _get_modulestore_by_type(self, modulestore_type):
        """
        This method should only really be used by tests and migration scripts when necessary.
        Returns the module store as requested by type.  The type can be a value from ModuleStoreEnum.Type.
        """
        for store in self.modulestores:
            if store.get_modulestore_type() == modulestore_type:
                return store
        return None

    def fill_in_run(self, course_key):
        """
        Some course_keys are used without runs. This function calls the corresponding
        fill_in_run function on the appropriate modulestore.
        """
        store = self._get_modulestore_for_courseid(course_key)
        if not hasattr(store, 'fill_in_run'):
            return course_key
        return store.fill_in_run(course_key)


    def has_item(self, usage_key, **kwargs):
        """
        Does the course include the xblock who's id is reference?
        """
        store = self._get_modulestore_for_courseid(usage_key.course_key)
        return store.has_item(usage_key, **kwargs)

    def get_item(self, usage_key, depth=0, **kwargs):
        """
        see parent doc
        """
        store = self._get_modulestore_for_courseid(usage_key.course_key)
        return store.get_item(usage_key, depth, **kwargs)

    def get_items(self, course_key, settings=None, content=None, **kwargs):
        """
        Returns:
            list of XModuleDescriptor instances for the matching items within the course with
            the given course_key

        NOTE: don't use this to look for courses
        as the course_key is required. Use get_courses.

        Args:
            course_key (CourseKey): the course identifier
            settings (dict): fields to look for which have settings scope. Follows same syntax
                and rules as kwargs below
            content (dict): fields to look for which have content scope. Follows same syntax and
                rules as kwargs below.
            kwargs (key=value): what to look for within the course.
                Common qualifiers are ``category`` or any field name. if the target field is a list,
                then it searches for the given value in the list not list equivalence.
                Substring matching pass a regex object.
                For some modulestores, ``name`` is another commonly provided key (Location based stores)
                For some modulestores,
                you can search by ``edited_by``, ``edited_on`` providing either a datetime for == (probably
                useless) or a function accepting one arg to do inequality
        """
        if not isinstance(course_key, CourseKey):
            raise Exception("Must pass in a course_key when calling get_items()")

        store = self._get_modulestore_for_courseid(course_key)
        return store.get_items(course_key, settings=settings, content=content, **kwargs)

    def get_courses(self):
        '''
        Returns a list containing the top level XModuleDescriptors of the courses in this modulestore.
        '''
        courses = {}  # a dictionary of course keys to course objects

        # first populate with the ones in mappings as the mapping override discovery
        for course_id, store in self.mappings.iteritems():
            course = store.get_course(course_id)
            # check if the course is not None - possible if the mappings file is outdated
            # TODO - log an error if the course is None, but move it to an initialization method to keep it less noisy
            if course is not None:
                courses[course_id] = course

        for store in self.modulestores:

            # filter out ones which were fetched from earlier stores but locations may not be ==
            for course in store.get_courses():
                course_id = self._clean_course_id_for_mapping(course.id)
                if course_id not in courses:
                    # course is indeed unique. save it in result
                    courses[course_id] = course

        return courses.values()

    def get_course(self, course_key, depth=0):
        """
        returns the course module associated with the course_id. If no such course exists,
        it returns None

        :param course_key: must be a CourseKey
        """
        assert(isinstance(course_key, CourseKey))
        store = self._get_modulestore_for_courseid(course_key)
        try:
            return store.get_course(course_key, depth=depth)
        except ItemNotFoundError:
            return None

    def has_course(self, course_id, ignore_case=False):
        """
        returns the course_id of the course if it was found, else None
        Note: we return the course_id instead of a boolean here since the found course may have
           a different id than the given course_id when ignore_case is True.

        Args:
        * course_id (CourseKey)
        * ignore_case (bool): If True, do a case insensitive search. If
            False, do a case sensitive search
        """
        assert(isinstance(course_id, CourseKey))
        store = self._get_modulestore_for_courseid(course_id)
        return store.has_course(course_id, ignore_case)

    def delete_course(self, course_key, user_id):
        """
        See xmodule.modulestore.__init__.ModuleStoreWrite.delete_course
        """
        assert(isinstance(course_key, CourseKey))
        store = self._get_modulestore_for_courseid(course_key)
        return store.delete_course(course_key, user_id)

    def get_parent_location(self, location, **kwargs):
        """
        returns the parent locations for a given location
        """
        store = self._get_modulestore_for_courseid(location.course_key)
        return store.get_parent_location(location, **kwargs)

    def get_modulestore_type(self, course_id):
        """
        Returns a type which identifies which modulestore is servicing the given course_id.
        The return can be one of:
        "xml" (for XML based courses),
        "mongo" for old-style MongoDB backed courses,
        "split" for new-style split MongoDB backed courses.
        """
        return self._get_modulestore_for_courseid(course_id).get_modulestore_type()

    def get_orphans(self, course_key):
        """
        Get all of the xblocks in the given course which have no parents and are not of types which are
        usually orphaned. NOTE: may include xblocks which still have references via xblocks which don't
        use children to point to their dependents.
        """
        store = self._get_modulestore_for_courseid(course_key)
        return store.get_orphans(course_key)

    def get_errored_courses(self):
        """
        Return a dictionary of course_dir -> [(msg, exception_str)], for each
        course_dir where course loading failed.
        """
        errs = {}
        for store in self.modulestores:
            errs.update(store.get_errored_courses())
        return errs

    def create_course(self, org, course, run, user_id, **kwargs):
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
        store = self._get_modulestore_for_courseid(None)
        return store.create_course(org, course, run, user_id, **kwargs)

    def clone_course(self, source_course_id, dest_course_id, user_id):
        """
        See the superclass for the general documentation.

        If cloning w/in a store, delegates to that store's clone_course which, in order to be self-
        sufficient, should handle the asset copying (call the same method as this one does)
        If cloning between stores,
            * copy the assets
            * migrate the courseware
        """
        source_modulestore = self._get_modulestore_for_courseid(source_course_id)
        # for a temporary period of time, we may want to hardcode dest_modulestore as split if there's a split
        # to have only course re-runs go to split. This code, however, uses the config'd priority
        dest_modulestore = self._get_modulestore_for_courseid(dest_course_id)
        if source_modulestore == dest_modulestore:
            return source_modulestore.clone_course(source_course_id, dest_course_id, user_id)

        # ensure super's only called once. The delegation above probably calls it; so, don't move
        # the invocation above the delegation call
        super(MixedModuleStore, self).clone_course(source_course_id, dest_course_id, user_id)

        if dest_modulestore.get_modulestore_type() == ModuleStoreEnum.Type.split:
            split_migrator = SplitMigrator(dest_modulestore, source_modulestore)
            split_migrator.migrate_mongo_course(
                source_course_id, user_id, dest_course_id.org, dest_course_id.course, dest_course_id.run
            )

    def create_item(self, user_id, course_key, block_type, block_id=None, fields=None, **kwargs):
        """
        Creates and saves a new item in a course.

        Returns the newly created item.

        Args:
            user_id: ID of the user creating and saving the xmodule
            course_key: A :class:`~opaque_keys.edx.CourseKey` identifying which course to create
                this item in
            block_type: The typo of block to create
            block_id: a unique identifier for the new item. If not supplied,
                a new identifier will be generated
            fields (dict): A dictionary specifying initial values for some or all fields
                in the newly created block
        """
        modulestore = self._verify_modulestore_support(course_key, 'create_item')
        return modulestore.create_item(user_id, course_key, block_type, block_id=block_id, fields=fields, **kwargs)

    def create_child(self, user_id, parent_usage_key, block_type, block_id=None, fields=None, **kwargs):
        """
        Creates and saves a new xblock that as a child of the specified block

        Returns the newly created item.

        Args:
            user_id: ID of the user creating and saving the xmodule
            parent_usage_key: a :class:`~opaque_key.edx.UsageKey` identifing the
                block that this item should be parented under
            block_type: The typo of block to create
            block_id: a unique identifier for the new item. If not supplied,
                a new identifier will be generated
            fields (dict): A dictionary specifying initial values for some or all fields
                in the newly created block
        """
        modulestore = self._verify_modulestore_support(parent_usage_key.course_key, 'create_child')
        return modulestore.create_child(user_id, parent_usage_key, block_type, block_id=block_id, fields=fields, **kwargs)

    def update_item(self, xblock, user_id, allow_not_found=False):
        """
        Update the xblock persisted to be the same as the given for all types of fields
        (content, children, and metadata) attribute the change to the given user.
        """
        store = self._verify_modulestore_support(xblock.location.course_key, 'update_item')
        return store.update_item(xblock, user_id, allow_not_found)

    def delete_item(self, location, user_id, **kwargs):
        """
        Delete the given item from persistence. kwargs allow modulestore specific parameters.
        """
        store = self._verify_modulestore_support(location.course_key, 'delete_item')
        store.delete_item(location, user_id=user_id, **kwargs)

    def revert_to_published(self, location, user_id):
        """
        Reverts an item to its last published version (recursively traversing all of its descendants).
        If no published version exists, a VersionConflictError is thrown.

        If a published version exists but there is no draft version of this item or any of its descendants, this
        method is a no-op.

        :raises InvalidVersionError: if no published version exists for the location specified
        """
        store = self._verify_modulestore_support(location.course_key, 'revert_to_published')
        return store.revert_to_published(location, user_id)

    def close_all_connections(self):
        """
        Close all db connections
        """
        for modulestore in self.modulestores:
            modulestore.close_connections()

    def _drop_database(self):
        """
        A destructive operation to drop all databases and close all db connections.
        Intended to be used by test code for cleanup.
        """
        for modulestore in self.modulestores:
            # drop database if the store supports it (read-only stores do not)
            if hasattr(modulestore, '_drop_database'):
                modulestore._drop_database()  # pylint: disable=protected-access

    def create_xmodule(self, location, definition_data=None, metadata=None, runtime=None, fields={}, **kwargs):
        """
        Create the new xmodule but don't save it. Returns the new module.

        :param location: a Location--must have a category
        :param definition_data: can be empty. The initial definition_data for the kvs
        :param metadata: can be empty, the initial metadata for the kvs
        :param runtime: if you already have an xblock from the course, the xblock.runtime value
        :param fields: a dictionary of field names and values for the new xmodule
        """
        store = self._verify_modulestore_support(location.course_key, 'create_xmodule')
        return store.create_xmodule(location, definition_data, metadata, runtime, fields, **kwargs)

    def get_courses_for_wiki(self, wiki_slug):
        """
        Return the list of courses which use this wiki_slug
        :param wiki_slug: the course wiki root slug
        :return: list of course locations
        """
        courses = []
        for modulestore in self.modulestores:
            courses.extend(modulestore.get_courses_for_wiki(wiki_slug))
        return courses

    def heartbeat(self):
        """
        Delegate to each modulestore and package the results for the caller.
        """
        # could be done in parallel threads if needed
        return dict(
            itertools.chain.from_iterable(
                store.heartbeat().iteritems()
                for store in self.modulestores
            )
        )

    def compute_publish_state(self, xblock):
        """
        Returns whether this xblock is draft, public, or private.

        Returns:
            PublishState.draft - content is in the process of being edited, but still has a previous
                version deployed to LMS
            PublishState.public - content is locked and deployed to LMS
            PublishState.private - content is editable and not deployed to LMS
        """
        course_id = xblock.scope_ids.usage_id.course_key
        store = self._get_modulestore_for_courseid(course_id)
        return store.compute_publish_state(xblock)

    def publish(self, location, user_id):
        """
        Save a current draft to the underlying modulestore
        Returns the newly published item.
        """
        store = self._verify_modulestore_support(location.course_key, 'publish')
        return store.publish(location, user_id)

    def unpublish(self, location, user_id):
        """
        Save a current draft to the underlying modulestore
        Returns the newly unpublished item.
        """
        store = self._verify_modulestore_support(location.course_key, 'unpublish')
        return store.unpublish(location, user_id)

    def convert_to_draft(self, location, user_id):
        """
        Create a copy of the source and mark its revision as draft.
        Note: This method is to support the Mongo Modulestore and may be deprecated.

        :param source: the location of the source (its revision must be None)
        """
        store = self._verify_modulestore_support(location.course_key, 'convert_to_draft')
        return store.convert_to_draft(location, user_id)

    def _verify_modulestore_support(self, course_key, method):
        """
        Finds and returns the store that contains the course for the given location, and verifying
        that the store supports the given method.

        Raises NotImplementedError if the found store does not support the given method.
        """
        store = self._get_modulestore_for_courseid(course_key)
        if hasattr(store, method):
            return store
        else:
            raise NotImplementedError(u"Cannot call {} on store {}".format(method, store))

    @contextmanager
    def default_store(self, store_type):
        """
        A context manager for temporarily changing the default store in the Mixed modulestore to the given store type
        """
        previous_store_list = self.modulestores
        found = False
        try:
            for i, store in enumerate(self.modulestores):
                if store.get_modulestore_type() == store_type:
                    self.modulestores.insert(0, self.modulestores.pop(i))
                    found = True
                    yield
            if not found:
                raise Exception(u"Cannot find store of type {}".format(store_type))
        finally:
            self.modulestores = previous_store_list

    @contextmanager
    def branch_setting(self, branch_setting, course_id=None):
        """
        A context manager for temporarily setting the branch value for the given course' store
        to the given branch_setting.  If course_id is None, the default store is used.
        """
        store = self._get_modulestore_for_courseid(course_id)
        with store.branch_setting(branch_setting, course_id):
            yield

    @contextmanager
    def bulk_write_operations(self, course_id):
        """
        A context manager for notifying the store of bulk write events.
        If course_id is None, the default store is used.
        """
        store = self._get_modulestore_for_courseid(course_id)
        with store.bulk_write_operations(course_id):
            yield
