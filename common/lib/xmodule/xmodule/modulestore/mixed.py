"""
MixedModuleStore allows for aggregation between multiple modulestores.

In this way, courses can be served up both - say - XMLModuleStore or MongoModuleStore

"""

from . import ModuleStoreWriteBase
from xmodule.modulestore.django import create_modulestore_instance, loc_mapper
import logging
from xmodule.modulestore import Location
from xblock.fields import Reference, ReferenceList, String
from xmodule.modulestore.locator import CourseLocator, Locator, BlockUsageLocator
from xmodule.modulestore.exceptions import InsufficientSpecificationError, ItemNotFoundError
from xmodule.modulestore.parsers import ALLOWED_ID_CHARS
import re

log = logging.getLogger(__name__)


class MixedModuleStore(ModuleStoreWriteBase):
    """
    ModuleStore knows how to route requests to the right persistence ms and how to convert any
    references in the xblocks to the type required by the app and the persistence layer.
    """
    def __init__(self, mappings, stores, reference_type=None, **kwargs):
        """
        Initialize a MixedModuleStore. Here we look into our passed in kwargs which should be a
        collection of other modulestore configuration informations

        :param reference_type: either Location or Locator to indicate what type of reference this app
        uses.
        """
        super(MixedModuleStore, self).__init__(**kwargs)

        self.modulestores = {}
        self.mappings = mappings
        # temporary code for transition period
        if reference_type is None:
            log.warn("reference_type not specified in MixedModuleStore settings. %s",
                "Will default temporarily to the to-be-deprecated Location.")
        self.use_locations = (reference_type != 'Locator')
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
                store['OPTIONS']
            )

    def _get_modulestore_for_courseid(self, course_id):
        """
        For a given course_id, look in the mapping table and see if it has been pinned
        to a particular modulestore
        """
        mapping = self.mappings.get(course_id, 'default')
        return self.modulestores[mapping]

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
        locator = loc_mapper().translate_location(course_id, reference, reference.revision == 'draft', True)
        return unicode(locator) if stringify else locator

    def _incoming_reference_adaptor(self, store, course_id, reference):
        """
        Convert the reference to the type the persistence layer wants
        """
        if issubclass(store.reference_type, Location if self.use_locations else Locator):
            return reference
        if store.reference_type == Location:
            return self._locator_to_location(reference)
        return self._location_to_locator(course_id, reference)

    def _outgoing_reference_adaptor(self, store, course_id, reference):
        """
        Convert the reference to the type the application wants
        """
        if issubclass(store.reference_type, Location if self.use_locations else Locator):
            return reference
        if store.reference_type == Location:
            return self._location_to_locator(course_id, reference)
        return self._locator_to_location(reference)

    def _xblock_adaptor_iterator(self, adaptor, string_converter, store, course_id, xblock):
        """
        Change all reference fields in this xblock to the type expected by the receiving layer
        """
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
            course_id, store.reference_type, xblock.location
        )
        return self._xblock_adaptor_iterator(
            self._incoming_reference_adaptor, string_converter, store, course_id, xblock
        )

    def _outgoing_xblock_adaptor(self, store, course_id, xblock):
        """
        Change all reference fields in this xblock to the type expected by the persistence layer
        """
        string_converter = self._get_string_converter(
            course_id, xblock.location.__class__, xblock.location
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
        if self.use_locations and reference_type == Location:
            return lambda field, xblock: None
        if not self.use_locations and issubclass(reference_type, Locator):
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
        # translate won't work w/ missing fields so work around it
        if store.reference_type == Location:
            if not self.use_locations:
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
            if self.use_locations:
                if not isinstance(location, Location):
                    location = Location(location)
                try:
                    location.ensure_fully_specified()
                    location = loc_mapper().translate_location(
                        course_id, location, location.revision == 'published', True
                    )
                except InsufficientSpecificationError:
                    # construct the Locator by hand
                    if location.category is not None and qualifiers.get('category', False):
                        qualifiers['category'] = location.category
                    location = loc_mapper().translate_location_to_course_locator(
                        course_id, location, location.revision == 'published'
                    )
        xblocks = store.get_items(location, course_id, depth, qualifiers)
        xblocks = [self._outgoing_xblock_adaptor(store, course_id, xblock) for xblock in xblocks]
        return xblocks

    def get_courses(self):
        '''
        Returns a list containing the top level XModuleDescriptors of the courses
        in this modulestore.
        '''
        courses = []
        for key in self.modulestores:
            store_courses = self.modulestores[key].get_courses()
            # If the store has not been labeled as 'default' then we should
            # only surface courses that have a mapping entry, for example the XMLModuleStore will
            # slurp up anything that is on disk, however, we don't want to surface those to
            # consumers *unless* there is an explicit mapping in the configuration
            if key != 'default':
                for course in store_courses:
                    # make sure that the courseId is mapped to the store in question
                    if key == self.mappings.get(course.location.course_id, 'default'):
                        courses = courses + ([course])
            else:
                # if we're the 'default' store provider, then we surface all courses hosted in
                # that store provider
                courses = courses + (store_courses)

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
                if not self.use_locations:
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
        return [self._outgoing_reference_adaptor(store, course_id, reference)
                for reference in parents]

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

    def update_item(self, xblock, user_id, allow_not_found=False):
        """
        Update the xblock persisted to be the same as the given for all types of fields
        (content, children, and metadata) attribute the change to the given user.
        """
        if self.use_locations:
            raise NotImplementedError

        locator = xblock.location
        course_id = locator.package_id
        store = self._get_modulestore_for_courseid(course_id)

        # if an xblock, convert its contents to correct addr scheme
        xblock = self._incoming_xblock_adaptor(store, course_id, xblock)
        xblock = store.update_item(xblock, user_id)

        return self._outgoing_xblock_adaptor(store, course_id, xblock)

    def delete_item(self, location, **kwargs):
        """
        Delete the given item from persistence.
        """
        if self.use_locations:
            raise NotImplementedError


    def close_all_connections(self):
        """
        Close all db connections
        """
        for mstore in self.modulestores:
            if hasattr(mstore, 'connection'):
                mstore.connection.close()
            elif hasattr(mstore, 'db'):
                mstore.db.connection.close()
