"""
MixedModuleStore allows for aggregation between multiple modulestores.

In this way, courses can be served up both - say - XMLModuleStore or MongoModuleStore

"""

import logging

from . import ModuleStoreWriteBase
from xmodule.modulestore.django import create_modulestore_instance, loc_mapper
from xmodule.modulestore import Location, SPLIT_MONGO_MODULESTORE_TYPE
from xmodule.modulestore.locator import CourseLocator
from xmodule.modulestore.exceptions import ItemNotFoundError, InvalidLocationError
from uuid import uuid4
from xmodule.modulestore.mongo.base import MongoModuleStore
from xmodule.modulestore.split_mongo.split import SplitMongoModuleStore

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
        self.mappings = mappings

        if 'default' not in stores:
            raise Exception('Missing a default modulestore in the MixedModuleStore __init__ method.')

        for key, store in stores.iteritems():
            is_xml = 'XMLModuleStore' in store['ENGINE']
            if is_xml:
                # restrict xml to only load courses in mapping
                store['OPTIONS']['course_ids'] = [
                    course_id
                    for course_id, store_key in self.mappings.iteritems()
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

    def has_item(self, course_id, reference):
        """
        Does the course include the xblock who's id is reference?

        :param course_id: a course_id or package_id (slashed or dotted)
        :param reference: a Location or BlockUsageLocator
        """
        store = self._get_modulestore_for_courseid(course_id)
        return store.has_item(course_id, reference)

    def get_item(self, location, depth=0):
        """
        This method is explicitly not implemented as we need a course_id to disambiguate
        We should be able to fix this when the data-model rearchitecting is done
        """
        # Although we shouldn't have both get_item and get_instance imho
        raise NotImplementedError

    def get_instance(self, course_id, location, depth=0):
        store = self._get_modulestore_for_courseid(course_id)
        return store.get_instance(course_id, location, depth)

    def get_items(self, location, course_id=None, depth=0, qualifiers=None):
        """
        Returns a list of XModuleDescriptor instances for the items
        that match location. Any element of location that is None is treated
        as a wildcard that matches any value. NOTE: don't use this to look for courses
        as the course_id is required. Use get_courses.

        location: either a Location possibly w/ None as wildcards for category or name or
        a Locator with at least a package_id and branch but possibly no block_id.

        depth: An argument that some module stores may use to prefetch
            descendants of the queried modules for more efficient results later
            in the request. The depth is counted in the number of calls to
            get_children() to cache. None indicates to cache all descendants
        """
        if not (course_id or hasattr(location, 'package_id')):
            raise Exception("Must pass in a course_id when calling get_items()")

        store = self._get_modulestore_for_courseid(course_id or getattr(location, 'package_id'))
        return store.get_items(location, course_id, depth, qualifiers)

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
        courses = {}  # a dictionary of stringified course locations to course objects
        # order the modulestores and ensure no dupes: an awkward bit of hardcoding to ensure precedence
        # xml is in here because mappings trump discovery
        if self.modulestores.has_key('xml'):
            stores = [self.modulestores['default'], self.modulestores['xml']]
        else:
            stores = [self.modulestores['default']]

        for key, store in self.modulestores.iteritems():
            # awkward hardcoding of knowledge that 'draft' is a dupe of 'direct'
            if key != 'draft' and store not in stores:
                stores.append(store)

        has_locators = False
        for store in stores:
            store_courses = store.get_courses()
            # filter out ones which were fetched from earlier stores but locations may not be ==
            for course in store_courses:
                course_location = unicode(course.location)
                if course_location not in courses:
                    if has_locators and isinstance(course.location, Location):
                        try:
                            # if there's no existing mapping, then the course can't have been in split
                            course_locator = loc_mapper().translate_location(
                                course.location.course_id, course.location, add_entry_if_missing=False
                            )
                            if unicode(course_locator) not in courses:
                                courses[course_location] = course
                        except ItemNotFoundError:
                            courses[course_location] = course
                    elif isinstance(course.location, CourseLocator):
                        has_locators = True
                        courses[course_location] = course
                    else:
                        courses[course_location] = course

        return courses.values()

    def get_course(self, course_id):
        """
        returns the course module associated with the course_id. If no such course exists,
        it returns None

        :param course_id: must be either a string course_id or a CourseLocator
        """
        store = self._get_modulestore_for_courseid(
            course_id.package_id if hasattr(course_id, 'package_id') else course_id
        )
        try:
            return store.get_course(course_id)
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

    def get_orphans(self, course_location, branch):
        """
        Get all of the xblocks in the given course which have no parents and are not of types which are
        usually orphaned. NOTE: may include xblocks which still have references via xblocks which don't
        use children to point to their dependents.
        """
        course_id = self._get_course_id_from_course_location(course_location)
        store = self._get_modulestore_for_courseid(course_id)
        return store.get_orphans(course_location, branch)

    def get_errored_courses(self):
        """
        Return a dictionary of course_dir -> [(msg, exception_str)], for each
        course_dir where course loading failed.
        """
        errs = {}
        for store in self.modulestores.values():
            errs.update(store.get_errored_courses())
        return errs

    def _get_course_id_from_block(self, block, store):
        """
        Get the course_id from the block or from asking its store. Expensive.
        """
        try:
            if block.course_id is not None:
                return block.course_id
        except AssertionError:  # will occur if no xmodule set
            pass
        try:
            course = store._get_course_for_item(block.scope_ids.usage_id)
            if course:
                return course.scope_ids.usage_id.course_id
        except:  # sorry, that method just raises vanilla Exception if it doesn't find course
            pass

    def _infer_course_id_try(self, location):
        """
        Create, Update, Delete operations don't require a fully-specified course_id, but
        there's no complete & sound general way to compute the course_id except via the
        proper modulestore. This method attempts several sound but not complete methods.
        :param location: an old style Location
        """
        if isinstance(location, CourseLocator):
            return location.package_id
        elif isinstance(location, basestring):
            try:
                location = Location(location)
            except InvalidLocationError:
                # try to parse as a course_id
                try:
                    Location.parse_course_id(location)
                    # it's already a course_id
                    return location
                except ValueError:
                    # cannot interpret the location
                    return None

        # location is a Location at this point
        if location.category == 'course':  # easiest case
            return location.course_id
        # try finding in loc_mapper
        try:
            # see if the loc mapper knows the course id (requires double translation)
            locator = loc_mapper().translate_location_to_course_locator(None, location)
            location = loc_mapper().translate_locator_to_location(locator, get_course=True)
            return location.course_id
        except ItemNotFoundError:
            pass
        # expensive query against all location-based modulestores to look for location.
        for store in self.modulestores.itervalues():
            if isinstance(location, store.reference_type):
                try:
                    xblock = store.get_item(location)
                    course_id = self._get_course_id_from_block(xblock, store)
                    if course_id is not None:
                        return course_id
                except NotImplementedError:
                    blocks = store.get_items(location)
                    if len(blocks) == 1:
                        block = blocks[0]
                        try:
                            if block.course_id is not None:
                                return block.course_id
                        except AssertionError:
                            pass
                except ItemNotFoundError:
                    pass
        # if we get here, it must be in a Locator based store, but we won't be able to find
        # it.
        return None

    def create_course(self, course_location, user_id=None, store_name='default', **kwargs):
        """
        Creates and returns the course. It creates a loc map from the course_location to
        the new one (if provided as id_root).

        NOTE: course_location must be a Location not
        a Locator until we no longer need to do loc mapping.

        NOTE: unlike the other mixed modulestore methods, this does not adapt its argument
        to the persistence store but requires its caller to know what the persistence store
        wants for args.

        :returns: course xblock
        """
        store = self.modulestores[store_name]
        if not hasattr(store, 'create_course'):
            raise NotImplementedError(u"Cannot create a course on store %s" % store_name)
        if store.get_modulestore_type(course_location.course_id) == SPLIT_MONGO_MODULESTORE_TYPE:
            org = kwargs.pop('org', course_location.org)
            pretty_id = kwargs.pop('pretty_id', None)
            fields = kwargs.get('fields', {})
            fields.update(kwargs.pop('metadata', {}))
            fields.update(kwargs.pop('definition_data', {}))
            kwargs['fields'] = fields
            # TODO rename id_root to package_id for consistency. It's too confusing
            id_root = kwargs.pop('id_root', u"{0.org}.{0.course}.{0.name}".format(course_location))
            course = store.create_course(
                org, pretty_id, user_id, id_root=id_root, master_branch=course_location.revision or 'published',
                **kwargs
            )
            block_map = {course_location.name: {'course': course.location.block_id}}
            # NOTE: course.location will be a Locator not == course_location
            loc_mapper().create_map_entry(
                course_location, course.location.package_id, block_map=block_map
            )
        else:  # assume mongo
            course = store.create_course(course_location, **kwargs)
            loc_mapper().translate_location(course_location.course_id, course_location)

        return course

    def create_item(self, course_or_parent_loc, category, user_id=None, **kwargs):
        """
        Create and return the item. If parent_loc is a specific location v a course id,
        it installs the new item as a child of the parent (if the parent_loc is a specific
        xblock reference).

        Adds an entry to the loc map using the kwarg location if provided (must be a
        Location if provided) or block_id and category if provided.

        :param course_or_parent_loc: Can be a course_id (org/course/run), CourseLocator,
        Location, or BlockUsageLocator but must be what the persistence modulestore expects
        """
        # find the store for the course
        course_id = self._infer_course_id_try(course_or_parent_loc)

        store = self._get_modulestore_for_courseid(course_id)

        location = kwargs.pop('location', None)
        # invoke its create_item
        if isinstance(store, MongoModuleStore):
            # convert parent loc if it's legit
            block_id = kwargs.pop('block_id', uuid4().hex)
            if isinstance(course_or_parent_loc, basestring):
                parent_loc = None
                if location is None:
                    locn_dict = Location.parse_course_id(course_id)
                    locn_dict['category'] = category
                    locn_dict['name'] = block_id
                    location = Location(locn_dict)
            else:
                parent_loc = course_or_parent_loc
                # must have a legitimate location, compute if appropriate
                if location is None:
                    location = parent_loc.replace(category=category, name=block_id)
            # do the actual creation
            xblock = store.create_and_save_xmodule(location, **kwargs)
            # add the loc mapping
            loc_mapper().translate_location(course_id, location)
            # don't forget to attach to parent
            if parent_loc is not None and not 'detached' in xblock._class_tags:
                parent = store.get_item(parent_loc)
                parent.children.append(location.url())
                store.update_item(parent)
        elif isinstance(store, SplitMongoModuleStore):
            if isinstance(course_or_parent_loc, basestring): # course_id
                old_course_id = course_or_parent_loc
                course_or_parent_loc = loc_mapper().translate_location_to_course_locator(
                    course_or_parent_loc, None
                )
            elif isinstance(course_or_parent_loc, CourseLocator):
                old_course_loc = loc_mapper().translate_locator_to_location(
                    course_or_parent_loc, get_course=True
                )
                old_course_id = old_course_loc.course_id
            else:
                raise ValueError(u"Cannot create a child of {} in split. Wrong repr.".format(course_or_parent_loc))

            # split handles all the fields in one dict not separated by scope
            fields = kwargs.get('fields', {})
            fields.update(kwargs.pop('metadata', {}))
            fields.update(kwargs.pop('definition_data', {}))
            kwargs['fields'] = fields

            xblock = store.create_item(course_or_parent_loc, category, user_id, **kwargs)
            if location is None:
                locn_dict = Location.parse_course_id(old_course_id)
                locn_dict['category'] = category
                locn_dict['name'] = xblock.location.block_id
                location = Location(locn_dict)
            # map location.name to xblock.location.block_id
            loc_mapper().translate_location(
                old_course_id, location, passed_block_id=xblock.location.block_id
            )
        else:
            raise NotImplementedError(u"Cannot create an item on store %s" % store)

        return xblock

    def update_item(self, xblock, user_id, allow_not_found=False):
        """
        Update the xblock persisted to be the same as the given for all types of fields
        (content, children, and metadata) attribute the change to the given user.
        """
        course_id = self._infer_course_id_try(xblock.scope_ids.usage_id)
        if course_id is None:
            raise ItemNotFoundError(u"Cannot find modulestore for %s" % xblock.scope_ids.usage_id)
        store = self._get_modulestore_for_courseid(course_id)
        return store.update_item(xblock, user_id)

    def delete_item(self, location, user_id=None):
        """
        Delete the given item from persistence.
        """
        course_id = self._infer_course_id_try(location)
        if course_id is None:
            raise ItemNotFoundError(u"Cannot find modulestore for %s" % location)
        store = self._get_modulestore_for_courseid(course_id)
        return store.delete_item(location, user_id=user_id)

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
            raise NotImplementedError(u"Cannot create maps from %s" % store.reference_type)
        for course in store.get_courses():
            loc_mapper().translate_location(course.location.course_id, course.location)
