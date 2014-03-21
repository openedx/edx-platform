"""
MixedModuleStore allows for aggregation between multiple modulestores.

In this way, courses can be served up both - say - XMLModuleStore or MongoModuleStore

"""

import logging

from . import ModuleStoreWriteBase
from xmodule.modulestore.django import create_modulestore_instance, loc_mapper
from xmodule.modulestore import Location, SPLIT_MONGO_MODULESTORE_TYPE, XML_MODULESTORE_TYPE
from xmodule.modulestore.locator import CourseLocator, Locator
from xmodule.modulestore.exceptions import ItemNotFoundError, InvalidLocationError
from xmodule.modulestore.keys import CourseKey
from uuid import uuid4
from xmodule.modulestore.mongo.base import MongoModuleStore
from xmodule.modulestore.split_mongo.split import SplitMongoModuleStore
from xmodule.exceptions import UndefinedContext

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
        self.mappings = {CourseKey.from_string(course_id): store_name for course_id, store_name in mappings.viewitems()}

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
            # If and when locations can identify their course, we won't need
            # these loc maps. They're needed for figuring out which store owns these locations.
            if is_xml:
                self.ensure_loc_maps_exist(key)

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

        :param course_id: a course_id or package_id (slashed or dotted)
        :param reference: a Location or BlockUsageLocator
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
                useless) or a tuple (">"|"<" datetime) for after or before, etc.
        """
        if not isinstance(course_key, CourseKey):
            raise Exception("Must pass in a course_key when calling get_items()")

        store = self._get_modulestore_for_courseid(course_key)
        return store.get_items(course_key, **kwargs)

    def _get_course_id_from_course_location(self, course_location):
        """
        Get the proper course_id based on the type of course_location
        """
        return getattr(course_location, 'course_id', None) or getattr(course_location, 'package_id', None)

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

    def get_parent_locations(self, location, course_id):
        """
        returns the parent locations for a given location and course_id
        """
        store = self._get_modulestore_for_courseid(course_id)
        return store.get_parent_locations(location, course_id)

    def get_modulestore_type(self, course_id):
        """
        Returns a type which identifies which modulestore is servicing the given course_id.
        The return can be one of:
        "xml" (for XML based courses),
        "mongo" for old-style MongoDB backed courses,
        "split" for new-style split MongoDB backed courses.
        """
        return self._get_modulestore_for_courseid(course_id).get_modulestore_type(course_id)

    def get_orphans(self, course_location):
        """
        Get all of the xblocks in the given course which have no parents and are not of types which are
        usually orphaned. NOTE: may include xblocks which still have references via xblocks which don't
        use children to point to their dependents.
        """
        course_id = self._get_course_id_from_course_location(course_location)
        store = self._get_modulestore_for_courseid(course_id)
        return store.get_orphans(course_location)

    def get_errored_courses(self):
        """
        Return a dictionary of course_dir -> [(msg, exception_str)], for each
        course_dir where course loading failed.
        """
        errs = {}
        for store in self.modulestores.values():
            errs.update(store.get_errored_courses())
        return errs

    def create_course(self, course_key, user_id=None, store_name='default', **kwargs):
        """
        Creates and returns the course.

        :param course_key: the CourseKey object for the course
        :param user_id: id of the user creating the course
        :param store_name: which datastore to use
        :returns: course
        """
        store = self.modulestores[store_name]
        if not hasattr(store, 'create_course'):
            raise NotImplementedError(u"Cannot create a course on store %s" % store_name)
        if store.get_modulestore_type(course_key) == SPLIT_MONGO_MODULESTORE_TYPE:
            org = kwargs.pop('org', course_key.org)
            fields = kwargs.pop('fields', {})
            fields.update(kwargs.pop('metadata', {}))
            fields.update(kwargs.pop('definition_data', {}))
            course = store.create_course(course_key, org, user_id, fields=fields, **kwargs)
        else:  # assume mongo
            course = store.create_course(course_key, **kwargs)

        return course

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
            # convert parent loc if it's legit
            if isinstance(course_or_parent_loc, basestring):
                parent_loc = None
                if location is None:
                    loc_dict = Location.parse_course_id(course_id)
                    loc_dict['name'] = block_id
                    location = Location(category=category, **loc_dict)
            else:
                parent_loc = course_or_parent_loc
                # must have a legitimate location, compute if appropriate
                if location is None:
                    location = parent_loc.replace(category=category, name=block_id)
            # do the actual creation
            xblock = store.create_and_save_xmodule(location, **kwargs)
            # don't forget to attach to parent
            if parent_loc is not None and not 'detached' in xblock._class_tags:
                parent = store.get_item(parent_loc)
                parent.children.append(location.url())
                store.update_item(parent)
        elif isinstance(store, SplitMongoModuleStore):
            if isinstance(course_or_parent_loc, basestring):  # course_id
                course_or_parent_loc = loc_mapper().translate_location_to_course_locator(
                    # hardcode draft version until we figure out how we're handling branches from app
                    course_or_parent_loc, None, published=False
                )
            elif not isinstance(course_or_parent_loc, CourseLocator):
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

    def ensure_loc_maps_exist(self, store_name):
        """
        Ensure location maps exist for every course in the modulestore whose
        name is the given name (mostly used for 'xml'). It creates maps for any
        missing ones.

        NOTE: will only work if the given store is Location based. If it's not,
        it raises NotImplementedError
        """
        store = self.modulestores[store_name]
        if store.reference_type != Location:
            raise ValueError(u"Cannot create maps from %s" % store.reference_type)
        for course in store.get_courses():
            loc_mapper().translate_location(course.location)

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
