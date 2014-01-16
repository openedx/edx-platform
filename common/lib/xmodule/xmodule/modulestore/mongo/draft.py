"""
A ModuleStore that knows about a special version 'draft'. Modules
marked as 'draft' are read in preference to modules without the 'draft'
version by this ModuleStore (so, access to i4x://org/course/cat/name
returns the i4x://org/course/cat/name@draft object if that exists,
and otherwise returns i4x://org/course/cat/name).
"""

from datetime import datetime

from xmodule.exceptions import InvalidVersionError
from xmodule.modulestore import Location
from xmodule.modulestore.exceptions import ItemNotFoundError, DuplicateItemError
from xmodule.modulestore.mongo.base import location_to_query, namedtuple_to_son, get_course_id_no_run, MongoModuleStore
import pymongo
from pytz import UTC

DRAFT = 'draft'
# Things w/ these categories should never be marked as version='draft'
DIRECT_ONLY_CATEGORIES = ['course', 'chapter', 'sequential', 'about', 'static_tab', 'course_info']


def as_draft(location):
    """
    Returns the Location that is the draft for `location`
    """
    return Location(location).replace(revision=DRAFT)


def as_published(location):
    """
    Returns the Location that is the published version for `location`
    """
    return Location(location).replace(revision=None)


def wrap_draft(item):
    """
    Sets `item.is_draft` to `True` if the item is a
    draft, and `False` otherwise. Sets the item's location to the
    non-draft location in either case
    """
    setattr(item, 'is_draft', item.location.revision == DRAFT)
    item.location = item.location.replace(revision=None)
    return item


class DraftModuleStore(MongoModuleStore):
    """
    This mixin modifies a modulestore to give it draft semantics.
    That is, edits made to units are stored to locations that have the revision DRAFT,
    and when reads are made, they first read with revision DRAFT, and then fall back
    to the baseline revision only if DRAFT doesn't exist.

    This module also includes functionality to promote DRAFT modules (and optionally
    their children) to published modules.
    """

    def get_item(self, location, depth=0):
        """
        Returns an XModuleDescriptor instance for the item at location.
        If location.revision is None, returns the item with the most
        recent revision

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

        try:
            return wrap_draft(super(DraftModuleStore, self).get_item(as_draft(location), depth=depth))
        except ItemNotFoundError:
            return wrap_draft(super(DraftModuleStore, self).get_item(location, depth=depth))

    def get_instance(self, course_id, location, depth=0):
        """
        Get an instance of this location, with policy for course_id applied.
        TODO (vshnayder): this may want to live outside the modulestore eventually
        """

        try:
            return wrap_draft(super(DraftModuleStore, self).get_instance(course_id, as_draft(location), depth=depth))
        except ItemNotFoundError:
            return wrap_draft(super(DraftModuleStore, self).get_instance(course_id, location, depth=depth))

    def create_xmodule(self, location, definition_data=None, metadata=None, system=None):
        """
        Create the new xmodule but don't save it. Returns the new module with a draft locator

        :param location: a Location--must have a category
        :param definition_data: can be empty. The initial definition_data for the kvs
        :param metadata: can be empty, the initial metadata for the kvs
        :param system: if you already have an xmodule from the course, the xmodule.system value
        """
        draft_loc = as_draft(location)
        if draft_loc.category in DIRECT_ONLY_CATEGORIES:
            raise InvalidVersionError(location)
        return super(DraftModuleStore, self).create_xmodule(draft_loc, definition_data, metadata, system)


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
        draft_loc = as_draft(location)

        draft_items = super(DraftModuleStore, self).get_items(draft_loc, course_id=course_id, depth=depth)
        items = super(DraftModuleStore, self).get_items(location, course_id=course_id, depth=depth)

        draft_locs_found = set(item.location.replace(revision=None) for item in draft_items)
        non_draft_items = [
            item
            for item in items
            if (item.location.revision != DRAFT
                and item.location.replace(revision=None) not in draft_locs_found)
        ]
        return [wrap_draft(item) for item in draft_items + non_draft_items]

    def convert_to_draft(self, source_location):
        """
        Create a copy of the source and mark its revision as draft.

        :param source: the location of the source (its revision must be None)
        """
        original = self.collection.find_one(location_to_query(source_location))
        draft_location = as_draft(source_location)
        if draft_location.category in DIRECT_ONLY_CATEGORIES:
            raise InvalidVersionError(source_location)
        if not original:
            raise ItemNotFoundError
        original['_id'] = namedtuple_to_son(draft_location)
        try:
            self.collection.insert(original)
        except pymongo.errors.DuplicateKeyError:
            raise DuplicateItemError(original['_id'])

        self.refresh_cached_metadata_inheritance_tree(draft_location)
        self.fire_updated_modulestore_signal(get_course_id_no_run(draft_location), draft_location)

        return self._load_items([original])[0]

    def update_item(self, xblock, user, allow_not_found=False):
        """
        Save the current values to persisted version of the xblock

        location: Something that can be passed to Location
        data: A nested dictionary of problem data
        """
        draft_loc = as_draft(xblock.location)
        try:
            if not self.has_item(None, draft_loc):
                self.convert_to_draft(xblock.location)
        except ItemNotFoundError, e:
            if not allow_not_found:
                raise e

        xblock.location = draft_loc
        super(DraftModuleStore, self).update_item(xblock, user)
        # don't allow locations to truly represent thenmselves as draft outside of this file
        xblock.location = as_published(xblock.location)

    def delete_item(self, location, delete_all_versions=False, **kwargs):
        """
        Delete an item from this modulestore

        location: Something that can be passed to Location
        """
        super(DraftModuleStore, self).delete_item(as_draft(location))
        if delete_all_versions:
            super(DraftModuleStore, self).delete_item(as_published(location))

        return

    def get_parent_locations(self, location, course_id):
        '''Find all locations that are the parents of this location.  Needed
        for path_to_location().

        returns an iterable of things that can be passed to Location.
        '''
        return super(DraftModuleStore, self).get_parent_locations(location, course_id)

    def publish(self, location, published_by_id):
        """
        Save a current draft to the underlying modulestore
        """
        try:
            original_published = super(DraftModuleStore, self).get_item(location)
        except ItemNotFoundError:
            original_published = None

        draft = self.get_item(location)

        draft.published_date = datetime.now(UTC)
        draft.published_by = published_by_id
        if draft.has_children:
            if original_published is not None:
                # see if children were deleted. 2 reasons for children lists to differ:
                #   1) child deleted
                #   2) child moved
                for child in original_published.children:
                    if child not in draft.children:
                        rents = [Location(mom) for mom in self.get_parent_locations(child, None)]
                        if (len(rents) == 1 and rents[0] == Location(location)):  # the 1 is this original_published
                            self.delete_item(child, True)
        super(DraftModuleStore, self).update_item(draft, None)
        self.delete_item(location)

    def unpublish(self, location):
        """
        Turn the published version into a draft, removing the published version
        """
        self.convert_to_draft(location)
        super(DraftModuleStore, self).delete_item(location)

    def _query_children_for_cache_children(self, items):
        # first get non-draft in a round-trip
        to_process_non_drafts = super(DraftModuleStore, self)._query_children_for_cache_children(items)

        to_process_dict = {}
        for non_draft in to_process_non_drafts:
            to_process_dict[Location(non_draft["_id"])] = non_draft

        # now query all draft content in another round-trip
        query = {
            '_id': {'$in': [namedtuple_to_son(as_draft(Location(item))) for item in items]}
        }
        to_process_drafts = list(self.collection.find(query))

        # now we have to go through all drafts and replace the non-draft
        # with the draft. This is because the semantics of the DraftStore is to
        # always return the draft - if available
        for draft in to_process_drafts:
            draft_loc = Location(draft["_id"])
            draft_as_non_draft_loc = draft_loc.replace(revision=None)

            # does non-draft exist in the collection
            # if so, replace it
            if draft_as_non_draft_loc in to_process_dict:
                to_process_dict[draft_as_non_draft_loc] = draft

        # convert the dict - which is used for look ups - back into a list
        queried_children = to_process_dict.values()

        return queried_children
