from datetime import datetime

from . import ModuleStoreBase, Location
from .exceptions import ItemNotFoundError

DRAFT = 'draft'


def as_draft(location):
    """
    Returns the Location that is the draft for `location`
    """
    return Location(location)._replace(revision=DRAFT)


def wrap_draft(item):
    """
    Sets `item.metadata['is_draft']` to `True` if the item is a
    draft, and false otherwise. Sets the item's location to the
    non-draft location in either case
    """
    item.metadata['is_draft'] = item.location.revision == DRAFT
    item.location = item.location._replace(revision=None)
    return item


class DraftModuleStore(ModuleStoreBase):
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
            return wrap_draft(super(DraftModuleStore, self).get_item(as_draft(location), depth))
        except ItemNotFoundError:
            return wrap_draft(super(DraftModuleStore, self).get_item(location, depth))

    def get_instance(self, course_id, location):
        """
        Get an instance of this location, with policy for course_id applied.
        TODO (vshnayder): this may want to live outside the modulestore eventually
        """
        try:
            return wrap_draft(super(DraftModuleStore, self).get_instance(course_id, as_draft(location)))
        except ItemNotFoundError:
            return wrap_draft(super(DraftModuleStore, self).get_instance(course_id, location))

    def get_items(self, location, depth=0):
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
        draft_items = super(DraftModuleStore, self).get_items(draft_loc, depth)
        items = super(DraftModuleStore, self).get_items(location, depth)

        draft_locs_found = set(item.location._replace(revision=None) for item in draft_items)
        non_draft_items = [
            item
            for item in items
            if (item.location.revision != DRAFT
                and item.location._replace(revision=None) not in draft_locs_found)
        ]
        return [wrap_draft(item) for item in draft_items + non_draft_items]

    def clone_item(self, source, location):
        """
        Clone a new item that is a copy of the item at the location `source`
        and writes it to `location`
        """
        return wrap_draft(super(DraftModuleStore, self).clone_item(source, as_draft(location)))

    def update_item(self, location, data):
        """
        Set the data in the item specified by the location to
        data

        location: Something that can be passed to Location
        data: A nested dictionary of problem data
        """
        draft_loc = as_draft(location)
        draft_item = self.get_item(location)
        if not draft_item.metadata['is_draft']:
            self.clone_item(location, draft_loc)

        return super(DraftModuleStore, self).update_item(draft_loc, data)

    def update_children(self, location, children):
        """
        Set the children for the item specified by the location to
        children

        location: Something that can be passed to Location
        children: A list of child item identifiers
        """
        draft_loc = as_draft(location)
        draft_item = self.get_item(location)
        if not draft_item.metadata['is_draft']:
            self.clone_item(location, draft_loc)

        return super(DraftModuleStore, self).update_children(draft_loc, children)

    def update_metadata(self, location, metadata):
        """
        Set the metadata for the item specified by the location to
        metadata

        location: Something that can be passed to Location
        metadata: A nested dictionary of module metadata
        """
        draft_loc = as_draft(location)
        draft_item = self.get_item(location)

        if not draft_item.metadata['is_draft']:
            self.clone_item(location, draft_loc)

        if 'is_draft' in metadata:
            del metadata['is_draft']

        return super(DraftModuleStore, self).update_metadata(draft_loc, metadata)

    def delete_item(self, location):
        """
        Delete an item from this modulestore

        location: Something that can be passed to Location
        """
        return super(DraftModuleStore, self).delete_item(as_draft(location))

    def get_parent_locations(self, location):
        '''Find all locations that are the parents of this location.  Needed
        for path_to_location().

        returns an iterable of things that can be passed to Location.
        '''
        return super(DraftModuleStore, self).get_parent_locations(location)

    def publish(self, location, published_by_id):
        """
        Save a current draft to the underlying modulestore
        """
        draft = self.get_item(location)
        metadata = {}
        metadata.update(draft.metadata)
        metadata['published_date'] = tuple(datetime.utcnow().timetuple())
        metadata['published_by'] = published_by_id
        super(DraftModuleStore, self).update_item(location, draft.definition.get('data', {}))
        super(DraftModuleStore, self).update_children(location, draft.definition.get('children', []))
        super(DraftModuleStore, self).update_metadata(location, metadata)
        self.delete_item(location)

    def unpublish(self, location):
        """
        Turn the published version into a draft, removing the published version
        """
        super(DraftModuleStore, self).clone_item(location, as_draft(location))
        super(DraftModuleStore, self).delete_item(location)
