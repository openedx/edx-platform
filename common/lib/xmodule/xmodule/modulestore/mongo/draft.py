"""
A ModuleStore that knows about a special version 'draft'. Modules
marked as 'draft' are read in preference to modules without the 'draft'
version by this ModuleStore (so, access to i4x://org/course/cat/name
returns the i4x://org/course/cat/name@draft object if that exists,
and otherwise returns i4x://org/course/cat/name).
"""

from datetime import datetime

from xmodule.exceptions import InvalidVersionError
from xmodule.modulestore.exceptions import ItemNotFoundError, DuplicateItemError
from xmodule.modulestore.mongo.base import location_to_query, MongoModuleStore
import pymongo
from pytz import UTC

DRAFT = 'draft'
# Things w/ these categories should never be marked as version='draft'
DIRECT_ONLY_CATEGORIES = ['course', 'chapter', 'sequential', 'about', 'static_tab', 'course_info']


def as_draft(location):
    """
    Returns the Location that is the draft for `location`
    """
    return location.replace(revision=DRAFT)


def as_published(location):
    """
    Returns the Location that is the published version for `location`
    """
    return location.replace(revision=None)


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

    def get_item(self, usage_key, depth=0):
        """
        Returns an XModuleDescriptor instance for the item at usage_key.
        If usage_key.revision is None, returns the item with the most
        recent revision

        If any segment of the usage_key is None except revision, raises
            xmodule.modulestore.exceptions.InsufficientSpecificationError

        If no object is found at that usage_key, raises
            xmodule.modulestore.exceptions.ItemNotFoundError

        usage_key: A :class:`.UsageKey` instance

        depth (int): An argument that some module stores may use to prefetch
            descendents of the queried modules for more efficient results later
            in the request. The depth is counted in the number of calls to
            get_children() to cache. None indicates to cache all descendents
        """

        try:
            return wrap_draft(super(DraftModuleStore, self).get_item(as_draft(usage_key), depth=depth))
        except ItemNotFoundError:
            return wrap_draft(super(DraftModuleStore, self).get_item(usage_key, depth=depth))

    def create_xmodule(self, location, definition_data=None, metadata=None, system=None, fields={}):
        """
        Create the new xmodule but don't save it. Returns the new module with a draft locator

        :param location: a Location--must have a category
        :param definition_data: can be empty. The initial definition_data for the kvs
        :param metadata: can be empty, the initial metadata for the kvs
        :param system: if you already have an xmodule from the course, the xmodule.system value
        """
        if location.category in DIRECT_ONLY_CATEGORIES:
            raise InvalidVersionError(location)
        draft_loc = as_draft(location)
        return super(DraftModuleStore, self).create_xmodule(draft_loc, definition_data, metadata, system, fields)

    def get_items(self, course_key, settings=None, content=None, **kwargs):
        """
        Returns:
            list of XModuleDescriptor instances for the matching items within the course with
            the given course_key

        NOTE: don't use this to look for courses
        as the course_key is required. Use get_courses.

        Args:
            course_key (CourseKey): the course identifier
            kwargs (key=value): what to look for within the course.
                Common qualifiers are ``category`` or any field name. if the target field is a list,
                then it searches for the given value in the list not list equivalence.
                Substring matching pass a regex object.
                ``name`` is another commonly provided key (Location based stores)
        """
        draft_items = [
            wrap_draft(item) for item in
            super(DraftModuleStore, self).get_items(course_key, revision='draft', **kwargs)
        ]
        draft_items_locations = {item.location for item in draft_items}
        non_draft_items = [
            item for item in
            super(DraftModuleStore, self).get_items(course_key, revision=None, **kwargs)
            # filter out items that are not already in draft
            if item.location not in draft_items_locations
        ]
        return draft_items + non_draft_items

    def convert_to_draft(self, source_location):
        """
        Create a copy of the source and mark its revision as draft.

        :param source: the location of the source (its revision must be None)
        """
        original = self.collection.find_one(location_to_query(source_location, wildcard=False))
        draft_location = as_draft(source_location)
        if draft_location.category in DIRECT_ONLY_CATEGORIES:
            raise InvalidVersionError(source_location)
        if not original:
            raise ItemNotFoundError(source_location)
        original['_id'] = draft_location.to_deprecated_son()
        try:
            self.collection.insert(original)
        except pymongo.errors.DuplicateKeyError:
            raise DuplicateItemError(original['_id'])

        self.refresh_cached_metadata_inheritance_tree(draft_location.course_key)

        return self._load_items(source_location.course_key, [original])[0]

    def update_item(self, xblock, user=None, allow_not_found=False):
        """
        Save the current values to persisted version of the xblock

        location: Something that can be passed to Location
        data: A nested dictionary of problem data
        """
        draft_loc = as_draft(xblock.location)
        try:
            if not self.has_item(draft_loc):
                self.convert_to_draft(xblock.location)
        except ItemNotFoundError:
            if not allow_not_found:
                raise

        xblock.location = draft_loc
        super(DraftModuleStore, self).update_item(xblock, user, allow_not_found)
        # don't allow locations to truly represent themselves as draft outside of this file
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
                        child_i4x = child
                        rents = self.get_parent_locations(child_i4x)
                        if (len(rents) == 1 and rents[0] == location):  # the 1 is this original_published
                            self.delete_item(child_i4x, True)
        super(DraftModuleStore, self).update_item(draft, '**replace_user**')
        self.delete_item(location)

    def unpublish(self, location):
        """
        Turn the published version into a draft, removing the published version
        """
        self.convert_to_draft(location)
        super(DraftModuleStore, self).delete_item(location)

    def _query_children_for_cache_children(self, course_key, items):
        # first get non-draft in a round-trip
        to_process_non_drafts = super(DraftModuleStore, self)._query_children_for_cache_children(course_key, items)

        to_process_dict = {}
        for non_draft in to_process_non_drafts:
            to_process_dict[self._location_from_id(non_draft["_id"], course_key.run)] = non_draft

        # now query all draft content in another round-trip
        query = {
            '_id': {'$in': [
                as_draft(course_key.make_usage_key_from_deprecated_string(item)).to_deprecated_son() for item in items
            ]}
        }
        to_process_drafts = list(self.collection.find(query))

        # now we have to go through all drafts and replace the non-draft
        # with the draft. This is because the semantics of the DraftStore is to
        # always return the draft - if available
        for draft in to_process_drafts:
            draft_loc = self._location_from_id(draft["_id"], course_key.run)
            draft_as_non_draft_loc = draft_loc.replace(revision=None)

            # does non-draft exist in the collection
            # if so, replace it
            if draft_as_non_draft_loc in to_process_dict:
                to_process_dict[draft_as_non_draft_loc] = draft

        # convert the dict - which is used for look ups - back into a list
        queried_children = to_process_dict.values()

        return queried_children
