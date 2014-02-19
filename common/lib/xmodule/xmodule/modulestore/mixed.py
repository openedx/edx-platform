"""
MixedModuleStore allows for aggregation between multiple modulestores.

In this way, courses can be served up both - say - XMLModuleStore or MongoModuleStore

"""

import re
from importlib import import_module
import logging
from xblock.fields import Reference, ReferenceList, String

from . import ModuleStoreWriteBase
from xmodule.modulestore.django import create_modulestore_instance, loc_mapper
from xmodule.modulestore import Location, SPLIT_MONGO_MODULESTORE_TYPE
from xmodule.modulestore.locator import CourseLocator, BlockUsageLocator
from xmodule.modulestore.exceptions import InsufficientSpecificationError, ItemNotFoundError
from xmodule.modulestore.parsers import ALLOWED_ID_CHARS
from uuid import uuid4

log = logging.getLogger(__name__)


class MixedModuleStore(ModuleStoreWriteBase):
    """
    ModuleStore knows how to route requests to the right persistence ms and how to convert any
    references in the xblocks to the type required by the app and the persistence layer.
    """
    def __init__(self, mappings, stores, reference_type=None, i18n_service=None, **kwargs):
        """
        Initialize a MixedModuleStore. Here we look into our passed in kwargs which should be a
        collection of other modulestore configuration informations

        :param reference_type: either a class object such as Locator or Location or the fully
        qualified dot-path to that class def to indicate what type of reference the app
        uses.
        """
        super(MixedModuleStore, self).__init__(**kwargs)

        self.modulestores = {}
        self.mappings = mappings
        # temporary code for transition period
        if reference_type is None:
            log.warn("reference_type not specified in MixedModuleStore settings. %s",
                "Will default temporarily to the to-be-deprecated Location.")
            self.reference_type = Location
        elif isinstance(reference_type, basestring):
            module_path, _, class_name = reference_type.rpartition('.')
            class_ = getattr(import_module(module_path), class_name)
            self.reference_type = class_
        else:
            self.reference_type = reference_type

        if 'default' not in stores:
            raise Exception('Missing a default modulestore in the MixedModuleStore __init__ method.')

        for key, store in stores.items():
            is_xml = 'XMLModuleStore' in store['ENGINE']
            if is_xml:
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
            # it would be better to have a notion of read-only rather than hardcode
            # key name
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

    # TODO move the location converters to a helper class which returns a converter object w/ 2
    # methods: convert_xblock and convert_reference. Then have mixed get the converter and use it.
    def _locator_to_location(self, reference):
        """
        Convert the referenced locator to a location casting to and from a string as necessary
        """
        stringify = isinstance(reference, basestring)
        if stringify:
            reference = BlockUsageLocator(url=reference)
        location = loc_mapper().translate_locator_to_location(reference)
        return location.url() if stringify else location

    def _location_to_locator(self, course_id, reference):
        """
        Convert the referenced location to a locator casting to and from a string as necessary
        """
        stringify = isinstance(reference, basestring)
        if stringify:
            reference = Location(reference)
        locator = loc_mapper().translate_location(course_id, reference, reference.revision == None, True)
        return unicode(locator) if stringify else locator

    def _incoming_reference_adaptor(self, store, course_id, reference):
        """
        Convert the reference to the type the persistence layer wants
        """
        if reference is None:
            return None
        if issubclass(store.reference_type, self.reference_type):
            return reference
        if store.reference_type == Location:
            return self._locator_to_location(reference)
        return self._location_to_locator(course_id, reference)

    def _outgoing_reference_adaptor(self, store, course_id, reference):
        """
        Convert the reference to the type the application wants
        """
        if reference is None:
            return None
        if issubclass(store.reference_type, self.reference_type):
            return reference
        if store.reference_type == Location:
            return self._location_to_locator(course_id, reference)
        return self._locator_to_location(reference)

    def _xblock_adaptor_iterator(self, adaptor, string_converter, store, course_id, xblock):
        """
        Change all reference fields in this xblock to the type expected by the receiving layer
        """
        xblock.location = adaptor(store, course_id, xblock.location)
        for field in xblock.fields.itervalues():
            if field.is_set_on(xblock):
                if isinstance(field, Reference):
                    field.write_to(
                        xblock,
                        adaptor(store, course_id, field.read_from(xblock))
                    )
                elif isinstance(field, ReferenceList):
                    field.write_to(
                        xblock,
                        [
                            adaptor(store, course_id, ref)
                            for ref in field.read_from(xblock)
                        ]
                    )
                elif isinstance(field, String):
                    # replace links within the string
                    string_converter(field, xblock)
        return xblock

    def _incoming_xblock_adaptor(self, store, course_id, xblock):
        """
        Change all reference fields in this xblock to the type expected by the persistence layer
        """
        string_converter = self._get_string_converter(
            course_id, store.reference_type, xblock.scope_ids.usage_id
        )
        return self._xblock_adaptor_iterator(
            self._incoming_reference_adaptor, string_converter, store, course_id, xblock
        )

    def _outgoing_xblock_adaptor(self, store, course_id, xblock):
        """
        Change all reference fields in this xblock to the type expected by the persistence layer
        """
        string_converter = self._get_string_converter(
            course_id, xblock.scope_ids.usage_id.__class__, xblock.scope_ids.usage_id
        )
        return self._xblock_adaptor_iterator(
            self._outgoing_reference_adaptor, string_converter, store, course_id, xblock
        )

    CONVERT_RE = re.compile(r"/jump_to_id/({}+)".format(ALLOWED_ID_CHARS))

    def _get_string_converter(self, course_id, reference_type, from_base_addr):
        """
        Return a closure which finds and replaces all embedded links in a string field
        with the correct rewritten link for the target type
        """
        if issubclass(self.reference_type, reference_type):
            return lambda field, xblock: None
        if isinstance(from_base_addr, Location):
            def mapper(found_id):
                """
                Convert the found id to BlockUsageLocator block_id
                """
                location = from_base_addr.replace(category=None, name=found_id)
                # NOTE without category, it cannot create a new mapping if there's not one already
                return loc_mapper().translate_location(course_id, location).block_id
        else:
            def mapper(found_id):
                """
                Convert the found id to Location block_id
                """
                locator = BlockUsageLocator.make_relative(from_base_addr, found_id)
                return loc_mapper().translate_locator_to_location(locator).name

        def converter(field, xblock):
            """
            Find all of the ids in the block and replace them w/ their mapped values
            """
            value = field.read_from(xblock)
            self.CONVERT_RE.sub(mapper, value)
            field.write_to(xblock, value)
        return converter

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
            raise NotImplementedError(u"Cannot create maps from %s", store.reference_type)
        for course in store.get_courses():
            loc_mapper().translate_location(course.location.course_id, course.location)

    def has_item(self, course_id, reference):
        """
        Does the course include the xblock who's id is reference?

        :param course_id: a course_id or package_id (slashed or dotted)
        :param reference: a Location or BlockUsageLocator
        """
        store = self._get_modulestore_for_courseid(course_id)
        decoded_ref = self._incoming_reference_adaptor(store, course_id, reference)
        return store.has_item(course_id, decoded_ref)

    def get_item(self, location, depth=0):
        """
        This method is explicitly not implemented as we need a course_id to disambiguate
        We should be able to fix this when the data-model rearchitecting is done
        """
        raise NotImplementedError

    def get_instance(self, course_id, location, depth=0):
        store = self._get_modulestore_for_courseid(course_id)
        decoded_ref = self._incoming_reference_adaptor(store, course_id, location)
        xblock = store.get_instance(course_id, decoded_ref, depth)
        return self._outgoing_xblock_adaptor(store, course_id, xblock)

    def get_items(self, location, course_id=None, depth=0, qualifiers=None):
        """
        Returns a list of XModuleDescriptor instances for the items
        that match location. Any element of location that is None is treated
        as a wildcard that matches any value. NOTE: don't use this to look for courses
        as the course_id is required. Use get_courses.

        location: either a Location possibly w/ None as wildcards for category or name or
        a Locator with at least a package_id and branch but possibly no block_id.

        depth: An argument that some module stores may use to prefetch
            descendents of the queried modules for more efficient results later
            in the request. The depth is counted in the number of calls to
            get_children() to cache. None indicates to cache all descendents
        """
        if not (course_id or hasattr(location, 'package_id')):
            raise Exception("Must pass in a course_id when calling get_items()")

        store = self._get_modulestore_for_courseid(course_id or getattr(location, 'package_id'))
        if not issubclass(self.reference_type, store.reference_type):
            if store.reference_type == Location:
                if getattr(location, 'block_id', False):
                    location = self._incoming_reference_adaptor(store, course_id, location)
                else:
                    # get the course's location
                    location = loc_mapper().translate_locator_to_location(location, get_course=True)
                    # now remove the unknowns
                    location = location.replace(
                        category=qualifiers.get('category', None),
                        name=None
                    )
            else:
                if not isinstance(location, Location):
                    location = Location(location)
                try:
                    location.ensure_fully_specified()
                    location = loc_mapper().translate_location(
                        course_id, location, location.revision == None, True
                    )
                except InsufficientSpecificationError:
                    # construct the Locator by hand
                    if location.category is not None and qualifiers.get('category', False):
                        qualifiers['category'] = location.category
                    location = loc_mapper().translate_location_to_course_locator(
                        course_id, location, location.revision == None
                    )
        xblocks = store.get_items(location, course_id, depth, qualifiers)
        xblocks = [self._outgoing_xblock_adaptor(store, course_id, xblock) for xblock in xblocks]
        return xblocks

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
        courses = []
        for key in self.modulestores:
            store = self.modulestores[key]
            store_courses = store.get_courses()
            # If the store has not been labeled as 'default' then we should
            # only surface courses that have a mapping entry, for example the XMLModuleStore will
            # slurp up anything that is on disk, however, we don't want to surface those to
            # consumers *unless* there is an explicit mapping in the configuration
            # TODO obviously this filtering only applies to filebased stores
            if key != 'default':
                for course in store_courses:
                    course_id = self._get_course_id_from_course_location(course.location)
                    # make sure that the courseId is mapped to the store in question
                    if key == self.mappings.get(course_id, 'default'):
                        courses.append(
                            self._outgoing_reference_adaptor(store, course_id, course.location)
                        )
            else:
                # if we're the 'default' store provider, then we surface all courses hosted in
                # that store provider
                store_courses = [
                    self._outgoing_reference_adaptor(
                        store, self._get_course_id_from_course_location(course.location), course.location
                    )
                    for course in store_courses
                ]
                courses = courses + store_courses

        return courses

    def get_course(self, course_id):
        """
        returns the course module associated with the course_id. If no such course exists,
        it returns None

        :param course_id: must be either a string course_id or a CourseLocator
        """
        store = self._get_modulestore_for_courseid(
            course_id.package_id if hasattr(course_id, 'package_id') else course_id)
        try:
            # translate won't work w/ missing fields so work around it
            if store.reference_type == Location:
                # takes the course_id: figure out if this is old or new style
                if not issubclass(store.reference_type, self.reference_type):
                    if isinstance(course_id, basestring):
                        course_id = CourseLocator(package_id=course_id, branch='published')
                    course_location = loc_mapper().translate_locator_to_location(course_id, get_course=True)
                    course_id = course_location.course_id
                xblock = store.get_course(course_id)
            else:
                # takes a courseLocator
                if isinstance(course_id, CourseLocator):
                    location = course_id
                    course_id = None  # not an old style course_id; so, don't use it further
                elif '/' in course_id:
                    location = loc_mapper().translate_location_to_course_locator(course_id, None, True)
                else:
                    location = CourseLocator(package_id=course_id, branch='published')
                    course_id = None  # not an old style course_id; so, don't use it further
                xblock = store.get_course(location)
        except ItemNotFoundError:
            return None
        if xblock is not None:
            return self._outgoing_xblock_adaptor(store, course_id, xblock)
        else:
            return None

    def get_parent_locations(self, location, course_id):
        """
        returns the parent locations for a given location and course_id
        """
        store = self._get_modulestore_for_courseid(course_id)
        decoded_ref = self._incoming_reference_adaptor(store, course_id, location)
        parents = store.get_parent_locations(decoded_ref, course_id)
        return [
            self._outgoing_reference_adaptor(store, course_id, reference)
            for reference in parents
        ]

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
        course_id = getattr(course_location, 'course_id', getattr(course_location, 'package_id', None))
        store = self._get_modulestore_for_courseid(course_id)
        decoded_ref = self._incoming_reference_adaptor(store, course_id, course_location)
        return store.get_orphans(decoded_ref, branch)

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
        if block.course_id is not None:
            return block.course_id
        try:
            course = store._get_course_for_item(block.scope_ids.usage_id)
            if course:
                return course.scope_ids.usage_id.course_id
        except:  # sorry, that method just raises vanilla Exception
            pass

    def _infer_course_id_try(self, location):
        """
        Create, Update, Delete operations don't require a fully-specified course_id, but
        there's no complete & sound general way to compute the course_id except via the
        proper modulestore. This method attempts several sound but not complete methods.
        :param location: an old style Location
        """
        if location.category == 'course':  # easiest case
            return location.course_id
        # try finding in loc_mapper
        try:
            locator = loc_mapper().translate_location_to_course_locator(None, location)
            location = loc_mapper().translate_locator_to_location(locator, get_course=True)
            return location.course_id
        except ItemNotFoundError:
            pass
        # expensive query against all location-based modulestores to look for location.
        for store in self.modulestores.itervalues():
            if isinstance(location, store.reference_type):
                try:
                    block = store.get_item(location)
                    course_id = self._get_course_id_from_block(block, store)
                    if course_id is not None:
                        return course_id
                except NotImplementedError:
                    blocks = store.get_items(location)
                    if len(blocks) == 1:
                        block = blocks[0]
                        if block.course_id is not None:
                            return block.course_id
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
        wants for args. It does not translate any references on the way in; so, don't
        pass children or other reference fields here.
        It does, however, adapt the xblock on the way out to the app's
        reference_type

        :returns: course xblock
        """
        store = self.modulestores[store_name]
        if not hasattr(store, 'create_course'):
            raise NotImplementedError(u"Cannot create a course on store %s", store_name)
        if store.get_modulestore_type(course_location.course_id) == SPLIT_MONGO_MODULESTORE_TYPE:
            org = kwargs.pop('org', course_location.org)
            pretty_id = kwargs.pop('pretty_id', None)
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

        return self._outgoing_xblock_adaptor(store, course_location.course_id, course)

    def create_item(self, course_or_parent_loc, category, user_id=None, **kwargs):
        """
        Create and return the item. If parent_loc is a specific location v a course id,
        it installs the new item as a child of the parent (if the parent_loc is a specific
        xblock reference).

        Adds an entry to the loc map using the kwarg location if provided (must be a
        Location if provided) or block_id and category if provided.

        :param course_or_parent_loc: will be translated appropriately to the course's store.
        Can be a course_id (org/course/run), CourseLocator, Location, or BlockUsageLocator.
        """
        # find the store for the course
        if self.reference_type == Location:
            if hasattr(course_or_parent_loc, 'tag'):
                course_id = self._infer_course_id_try(course_or_parent_loc)
            else:
                course_id = course_or_parent_loc
        else:
            course_id = course_or_parent_loc.package_id
        store = self._get_modulestore_for_courseid(course_id)

        location = kwargs.pop('location', None)
        # invoke its create_item
        if store.reference_type == Location:
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
                parent_loc = self._incoming_reference_adaptor(store, course_id, course_or_parent_loc)
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
        else:
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
            else:  # it's a Location
                old_course_id = course_id
                course_or_parent_loc = self._location_to_locator(course_id, course_or_parent_loc)
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
        return xblock

    def update_item(self, xblock, user_id, allow_not_found=False):
        """
        Update the xblock persisted to be the same as the given for all types of fields
        (content, children, and metadata) attribute the change to the given user.
        """
        if self.reference_type == Location:
            course_id = xblock.course_id
            if course_id is None:
                course_id = self._infer_course_id_try(xblock.scope_ids.usage_id)
                if course_id is None:
                    raise ItemNotFoundError(u"Cannot find modulestore for %s", xblock.scope_ids.usage_id)
        else:
            locator = xblock.scope_ids.usage_id
            course_id = locator.package_id
        store = self._get_modulestore_for_courseid(course_id)

        # if an xblock, convert its contents to correct addr scheme
        xblock = self._incoming_xblock_adaptor(store, course_id, xblock)
        xblock = store.update_item(xblock, user_id)

        return self._outgoing_xblock_adaptor(store, course_id, xblock)

    def delete_item(self, location, user_id=None):
        """
        Delete the given item from persistence.
        """
        if self.reference_type == Location:
            course_id = self._infer_course_id_try(location)
            if course_id is None:
                raise ItemNotFoundError(u"Cannot find modulestore for %s", location)
        else:
            course_id = location.package_id
        store = self._get_modulestore_for_courseid(course_id)

        decoded_ref = self._incoming_reference_adaptor(store, course_id, location)
        return store.delete_item(decoded_ref, user_id=user_id)

    def close_all_connections(self):
        """
        Close all db connections
        """
        for mstore in self.modulestores.itervalues():
            if hasattr(mstore, 'database'):
                mstore.database.connection.close()
            elif hasattr(mstore, 'db'):
                mstore.db.connection.close()

