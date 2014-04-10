"""
MixedModuleStore allows for aggregation between multiple modulestores.

In this way, courses can be served up both - say - XMLModuleStore or MongoModuleStore

"""

import logging
from uuid import uuid4
from opaque_keys import InvalidKeyError

from . import ModuleStoreWriteBase
from xmodule.modulestore.django import create_modulestore_instance, loc_mapper
from xmodule.modulestore import Location, XML_MODULESTORE_TYPE
from xmodule.modulestore.locator import CourseLocator, Locator, BlockUsageLocator
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.keys import CourseKey, UsageKey
from xmodule.modulestore.mongo.base import MongoModuleStore
from xmodule.modulestore.split_mongo.split import SplitMongoModuleStore
from xmodule.modulestore.locations import SlashSeparatedCourseKey

log = logging.getLogger(__name__)


class MixedModuleStore(ModuleStoreWriteBase):
    """
    ModuleStore knows how to route requests to the right persistence ms
    """
    def __init__(self, mappings, stores, i18n_service=None, **kwargs):
        """
        Initialize a MixedModuleStore. Here we look into our passed in kwargs which should be a
        collection of other modulestore configuration informations
        """
        super(MixedModuleStore, self).__init__(**kwargs)

        self.modulestores = {}
        self.mappings = {}

        for course_id, store_name in mappings.iteritems():
            try:
                self.mappings[CourseKey.from_string(course_id)] = store_name
            except InvalidKeyError:
                self.mappings[SlashSeparatedCourseKey.from_deprecated_string(course_id)] = store_name

        if 'default' not in stores:
            raise Exception('Missing a default modulestore in the MixedModuleStore __init__ method.')

        for key, store in stores.iteritems():
            is_xml = 'XMLModuleStore' in store['ENGINE']
            if is_xml:
                # restrict xml to only load courses in mapping
                store['OPTIONS']['course_ids'] = [
                    course_id
                    for course_id, store_key in mappings.iteritems()
                    if store_key == key
                ]
            self.modulestores[key] = create_modulestore_instance(
                store['ENGINE'],
                # XMLModuleStore's don't have doc store configs
                store.get('DOC_STORE_CONFIG', {}),
                store['OPTIONS'],
                i18n_service=i18n_service,
            )

    def _get_modulestore_for_courseid(self, course_id):
        """
        For a given course_id, look in the mapping table and see if it has been pinned
        to a particular modulestore
        """
        # TODO when this becomes a router capable of handling more than one r/w backend
        # we'll need to generalize this to handle mappings from old Locations w/o full
        # course_id in much the same way as loc_mapper().translate_location does.
        mapping = self.mappings.get(course_id, 'default')
        return self.modulestores[mapping]

    def has_item(self, usage_key):
        """
        Does the course include the xblock who's id is reference?
        """
        store = self._get_modulestore_for_courseid(usage_key.course_key)
        return store.has_item(usage_key)

    def get_item(self, usage_key, depth=0):
        """
        This method is explicitly not implemented as we need a course_id to disambiguate
        We should be able to fix this when the data-model rearchitecting is done
        """
        store = self._get_modulestore_for_courseid(usage_key.course_key)
        return store.get_item(usage_key, depth)

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
        return store.get_items(course_key, **kwargs)

    def get_courses(self):
        '''
        Returns a list containing the top level XModuleDescriptors of the courses
        in this modulestore.
        '''
        # order the modulestores and ensure no dupes (default may be a dupe of a named store)
        # remove 'draft' as we know it's a functional dupe of 'direct' (ugly hardcoding)
        stores = set([value for key, value in self.modulestores.iteritems() if key != 'draft'])
        stores = sorted(stores, cmp=_compare_stores)

        courses = {}  # a dictionary of stringified course locations to course objects
        has_locators = any(issubclass(CourseLocator, store.reference_type) for store in stores)
        for store in stores:
            store_courses = store.get_courses()
            # filter out ones which were fetched from earlier stores but locations may not be ==
            for course in store_courses:
                course_location = unicode(course.location)
                if course_location not in courses:
                    if has_locators and isinstance(course.location, Location):
                        # see if a locator version of course is in the result
                        try:
                            # if there's no existing mapping, then the course can't have been in split
                            course_locator = loc_mapper().translate_location(
                                course.location,
                                add_entry_if_missing=False
                            )
                            if unicode(course_locator) not in courses:
                                courses[course_location] = course
                        except ItemNotFoundError:
                            courses[course_location] = course
                    else:
                        courses[course_location] = course

        return courses.values()

    def get_course(self, course_id, depth=None):
        """
        returns the course module associated with the course_id. If no such course exists,
        it returns None

        :param course_id: must be either a string course_id or a CourseLocator
        """
        assert(isinstance(course_id, CourseKey))
        store = self._get_modulestore_for_courseid(course_id)
        try:
            return store.get_course(course_id, depth=depth)
        except ItemNotFoundError:
            return None

    def has_course(self, course_id, ignore_case=False):
        """
        returns whether the course exists

        Args:
        * course_id (CourseKey)
        """
        assert(isinstance(course_id, CourseKey))
        store = self._get_modulestore_for_courseid(course_id)
        return store.has_course(course_id, ignore_case)

    def delete_course(self, course_key, user_id=None):
        """
        Remove the given course from its modulestore.
        """
        assert(isinstance(course_key, CourseKey))
        store = self._get_modulestore_for_courseid(course_key)
        return store.delete_course(course_key, user_id)

    def get_parent_locations(self, location):
        """
        returns the parent locations for a given location and course_id
        """
        store = self._get_modulestore_for_courseid(location.course_key)
        return store.get_parent_locations(location)

    def get_modulestore_type(self, course_id):
        """
        Returns a type which identifies which modulestore is servicing the given course_id.
        The return can be one of:
        "xml" (for XML based courses),
        "mongo" for old-style MongoDB backed courses,
        "split" for new-style split MongoDB backed courses.
        """
        return self._get_modulestore_for_courseid(course_id).get_modulestore_type(course_id)

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
        for store in self.modulestores.values():
            errs.update(store.get_errored_courses())
        return errs

    def create_course(self, org, offering, user_id=None, fields=None, store_name='default', **kwargs):
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
        store = self.modulestores[store_name]

        if not hasattr(store, 'create_course'):
            raise NotImplementedError(u"Cannot create a course on store %s" % store_name)

        return store.create_course(org, offering, user_id, fields, **kwargs)

    def create_item(self, course_or_parent_loc, category, user_id=None, **kwargs):
        """
        Create and return the item. If parent_loc is a specific location v a course id,
        it installs the new item as a child of the parent (if the parent_loc is a specific
        xblock reference).

        :param course_or_parent_loc: Can be a CourseKey or UsageKey
        """
        # find the store for the course
        course_id = getattr(course_or_parent_loc, 'course_key', course_or_parent_loc)
        store = self._get_modulestore_for_courseid(course_id)

        location = kwargs.pop('location', None)
        # invoke its create_item
        if isinstance(store, MongoModuleStore):
            block_id = kwargs.pop('block_id', getattr(location, 'name', uuid4().hex))
            parent_loc = course_or_parent_loc if isinstance(course_or_parent_loc, UsageKey) else None
            # must have a legitimate location, compute if appropriate
            if location is None:
                location = course_id.make_usage_key(category, block_id)
            # do the actual creation
            xblock = store.create_and_save_xmodule(location, **kwargs)
            # don't forget to attach to parent
            if parent_loc is not None and not 'detached' in xblock._class_tags:
                parent = store.get_item(parent_loc)
                parent.children.append(location)
                store.update_item(parent)
        elif isinstance(store, SplitMongoModuleStore):
            if not isinstance(course_or_parent_loc, (CourseLocator, BlockUsageLocator)):
                raise ValueError(u"Cannot create a child of {} in split. Wrong repr.".format(course_or_parent_loc))

            # split handles all the fields in one dict not separated by scope
            fields = kwargs.get('fields', {})
            fields.update(kwargs.pop('metadata', {}))
            fields.update(kwargs.pop('definition_data', {}))
            kwargs['fields'] = fields

            xblock = store.create_item(course_or_parent_loc, category, user_id, **kwargs)
        else:
            raise NotImplementedError(u"Cannot create an item on store %s" % store)

        return xblock

    def update_item(self, xblock, user_id, allow_not_found=False):
        """
        Update the xblock persisted to be the same as the given for all types of fields
        (content, children, and metadata) attribute the change to the given user.
        """
        course_id = xblock.scope_ids.usage_id.course_key
        store = self._get_modulestore_for_courseid(course_id)
        return store.update_item(xblock, user_id)

    def delete_item(self, location, user_id=None, **kwargs):
        """
        Delete the given item from persistence. kwargs allow modulestore specific parameters.
        """
        course_id = location.course_key
        store = self._get_modulestore_for_courseid(course_id)
        return store.delete_item(location, user_id=user_id, **kwargs)

    def close_all_connections(self):
        """
        Close all db connections
        """
        for mstore in self.modulestores.itervalues():
            if hasattr(mstore, 'database'):
                mstore.database.connection.close()
            elif hasattr(mstore, 'db'):
                mstore.db.connection.close()

    def get_courses_for_wiki(self, wiki_slug):
        """
        Return the list of courses which use this wiki_slug
        :param wiki_slug: the course wiki root slug
        :return: list of course locations
        """
        courses = []
        for modulestore in self.modulestores.values():
            courses.extend(modulestore.get_courses_for_wiki(wiki_slug))
        return courses


def _compare_stores(left, right):
    """
    Order stores via precedence: if a course is found in an earlier store, it shadows the later store.

    xml stores take precedence b/c they only contain hardcoded mappings, then Locator-based ones,
    then others. Locators before Locations because if some courses may be in both,
    the ones in the Locator-based stores shadow the others.
    """
    if left.get_modulestore_type(None) == XML_MODULESTORE_TYPE:
        if right.get_modulestore_type(None) == XML_MODULESTORE_TYPE:
            return 0
        else:
            return -1
    elif right.get_modulestore_type(None) == XML_MODULESTORE_TYPE:
        return 1

    if issubclass(left.reference_type, Locator):
        if issubclass(right.reference_type, Locator):
            return 0
        else:
            return -1
    elif issubclass(right.reference_type, Locator):
        return 1

    return 0
