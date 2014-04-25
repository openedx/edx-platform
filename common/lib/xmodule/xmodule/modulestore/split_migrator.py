'''
Code for migrating from other modulestores to the split_mongo modulestore.

Exists at the top level of modulestore b/c it needs to know about and access each modulestore.

In general, it's strategy is to treat the other modulestores as read-only and to never directly
manipulate storage but use existing api's.
'''
from xblock.fields import Reference, ReferenceList, ReferenceValueDict


class SplitMigrator(object):
    """
    Copies courses from old mongo to split mongo and sets up location mapping so any references to the old
    name will be able to find the new elements.
    """
    def __init__(self, split_modulestore, direct_modulestore, draft_modulestore, loc_mapper):
        super(SplitMigrator, self).__init__()
        self.split_modulestore = split_modulestore
        self.direct_modulestore = direct_modulestore
        self.draft_modulestore = draft_modulestore
        self.loc_mapper = loc_mapper

    def migrate_mongo_course(self, course_key, user, new_org=None, new_offering=None):
        """
        Create a new course in split_mongo representing the published and draft versions of the course from the
        original mongo store. And return the new CourseLocator

        If the new course already exists, this raises DuplicateItemError

        :param course_location: a Location whose category is 'course' and points to the course
        :param user: the user whose action is causing this migration
        :param new_org: (optional) the Locator.org for the new course. Defaults to
        whatever translate_location_to_locator returns
        """
        new_course_locator = self.loc_mapper.create_map_entry(course_key, new_org, new_offering)
        # the only difference in data between the old and split_mongo xblocks are the locations;
        # so, any field which holds a location must change to a Locator; otherwise, the persistence
        # layer and kvs's know how to store it.
        # locations are in location, children, conditionals, course.tab

        # create the course: set fields to explicitly_set for each scope, id_root = new_course_locator, master_branch = 'production'
        original_course = self.direct_modulestore.get_course(course_key)
        new_course_root_locator = self.loc_mapper.translate_location(original_course.location)
        new_course = self.split_modulestore.create_course(
            new_course_root_locator.org, new_course_root_locator.offering, user.id,
            fields=self._get_json_fields_translate_references(original_course, course_key, True),
            root_block_id=new_course_root_locator.block_id,
            master_branch=new_course_root_locator.branch
        )

        self._copy_published_modules_to_course(new_course, original_course.location, course_key, user)
        self._add_draft_modules_to_course(new_course.id, course_key, user)

        return new_course_locator

    def _copy_published_modules_to_course(self, new_course, old_course_loc, course_key, user):
        """
        Copy all of the modules from the 'direct' version of the course to the new split course.
        """
        course_version_locator = new_course.id

        # iterate over published course elements. Wildcarding rather than descending b/c some elements are orphaned (e.g.,
        # course about pages, conditionals)
        for module in self.direct_modulestore.get_items(course_key):
            # don't copy the course again. No drafts should get here but check
            if module.location != old_course_loc and not getattr(module, 'is_draft', False):
                # create split_xblock using split.create_item
                # where block_id is computed by translate_location_to_locator
                new_locator = self.loc_mapper.translate_location(
                    module.location, True, add_entry_if_missing=True
                )
                # NOTE: the below auto populates the children when it migrates the parent; so,
                # it doesn't need the parent as the first arg. That is, it translates and populates
                # the 'children' field as it goes.
                _new_module = self.split_modulestore.create_item(
                    course_version_locator, module.category, user.id,
                    block_id=new_locator.block_id,
                    fields=self._get_json_fields_translate_references(module, course_key, True),
                    continue_version=True
                )
        # after done w/ published items, add version for 'draft' pointing to the published structure
        index_info = self.split_modulestore.get_course_index_info(course_version_locator)
        versions = index_info['versions']
        versions['draft'] = versions['published']
        self.split_modulestore.update_course_index(index_info)

        # clean up orphans in published version: in old mongo, parents pointed to the union of their published and draft
        # children which meant some pointers were to non-existent locations in 'direct'
        self.split_modulestore.internal_clean_children(course_version_locator)

    def _add_draft_modules_to_course(self, published_course_key, course_key, user):
        """
        update each draft. Create any which don't exist in published and attach to their parents.
        """
        # each true update below will trigger a new version of the structure. We may want to just have one new version
        # but that's for a later date.
        new_draft_course_loc = published_course_key.for_branch('draft')
        # to prevent race conditions of grandchilden being added before their parents and thus having no parent to
        # add to
        awaiting_adoption = {}
        for module in self.draft_modulestore.get_items(course_key):
            if getattr(module, 'is_draft', False):
                new_locator = self.loc_mapper.translate_location(
                    module.location, False, add_entry_if_missing=True
                )
                if self.split_modulestore.has_item(new_locator):
                    # was in 'direct' so draft is a new version
                    split_module = self.split_modulestore.get_item(new_locator)
                    # need to remove any no-longer-explicitly-set values and add/update any now set values.
                    for name, field in split_module.fields.iteritems():
                        if field.is_set_on(split_module) and not module.fields[name].is_set_on(module):
                            field.delete_from(split_module)
                    for name, field in module.fields.iteritems():
                        # draft children will insert themselves and the others are here already; so, don't do it 2x
                        if name != 'children' and field.is_set_on(module):
                            field.write_to(split_module, field.read_from(module))

                    _new_module = self.split_modulestore.update_item(split_module, user.id)
                else:
                    # only a draft version (aka, 'private'). parent needs updated too.
                    # create a new course version just in case the current head is also the prod head
                    _new_module = self.split_modulestore.create_item(
                        new_draft_course_loc, module.category, user.id,
                        block_id=new_locator.block_id,
                        fields=self._get_json_fields_translate_references(module, course_key, True)
                    )
                    awaiting_adoption[module.location] = new_locator.block_id
        for draft_location, new_block_id in awaiting_adoption.iteritems():
            for parent_loc in self.draft_modulestore.get_parent_locations(draft_location):
                old_parent = self.draft_modulestore.get_item(parent_loc)
                new_parent = self.split_modulestore.get_item(
                    self.loc_mapper.translate_location(old_parent.location, False)
                )
                # this only occurs if the parent was also awaiting adoption
                if new_block_id in new_parent.children:
                    break
                # find index for module: new_parent may be missing quite a few of old_parent's children
                new_parent_cursor = 0
                for old_child_loc in old_parent.children:
                    if old_child_loc == draft_location:
                        break
                    sibling_loc = self.loc_mapper.translate_location(old_child_loc, False)
                    # sibling may move cursor
                    for idx in range(new_parent_cursor, len(new_parent.children)):
                        if new_parent.children[idx] == sibling_loc.block_id:
                            new_parent_cursor = idx + 1
                            break
                new_parent.children.insert(new_parent_cursor, new_block_id)
                new_parent = self.split_modulestore.update_item(new_parent, user.id)

    def _get_json_fields_translate_references(self, xblock, old_course_id, published):
        """
        Return the json repr for explicitly set fields but convert all references to their block_id's
        """
        # FIXME change split to take field values as pythonic values not json values
        result = {}
        for field_name, field in xblock.fields.iteritems():
            if field.is_set_on(xblock):
                if isinstance(field, Reference):
                    result[field_name] = unicode(self.loc_mapper.translate_location(
                        getattr(xblock, field_name), published, add_entry_if_missing=True
                    ))
                elif isinstance(field, ReferenceList):
                    result[field_name] = [
                        unicode(self.loc_mapper.translate_location(
                            ele, published, add_entry_if_missing=True
                        )) for ele in getattr(xblock, field_name)
                    ]
                elif isinstance(field, ReferenceValueDict):
                    result[field_name] = {
                        key: unicode(self.loc_mapper.translate_location(
                            subvalue, published, add_entry_if_missing=True
                        ))
                        for key, subvalue in getattr(xblock, field_name).iteritems()
                    }
                else:
                    result[field_name] = field.read_json(xblock)

        return result
