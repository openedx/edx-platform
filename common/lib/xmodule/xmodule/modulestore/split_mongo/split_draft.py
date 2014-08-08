"""
Module for the dual-branch fall-back Draft->Published Versioning ModuleStore
"""

from split import SplitMongoModuleStore, EXCLUDE_ALL
from xmodule.modulestore import ModuleStoreEnum, PublishState
from xmodule.modulestore.exceptions import InsufficientSpecificationError
from xmodule.modulestore.draft_and_published import (
    ModuleStoreDraftAndPublished, DIRECT_ONLY_CATEGORIES, UnsupportedRevisionError
)


class DraftVersioningModuleStore(ModuleStoreDraftAndPublished, SplitMongoModuleStore):
    """
    A subclass of Split that supports a dual-branch fall-back versioning framework
        with a Draft branch that falls back to a Published branch.
    """
    def create_course(self, org, course, run, user_id, skip_auto_publish=False, **kwargs):
        """
        Creates and returns the course.

        Args:
            org (str): the organization that owns the course
            course (str): the name of the course
            run (str): the name of the run
            user_id: id of the user creating the course
            kwargs: Any optional arguments understood by a subset of modulestores to customize instantiation

        Returns: a CourseDescriptor
        """
        master_branch = kwargs.pop('master_branch', ModuleStoreEnum.BranchName.draft)
        item = super(DraftVersioningModuleStore, self).create_course(
            org, course, run, user_id, master_branch=master_branch, **kwargs
        )
        if master_branch == ModuleStoreEnum.BranchName.draft and not skip_auto_publish:
            # any other value is hopefully only cloning or doing something which doesn't want this value add
            self._auto_publish_no_children(item.location, item.location.category, user_id, **kwargs)

            # create any other necessary things as a side effect: ensure they populate the draft branch
            # and rely on auto publish to populate the published branch: split's create course doesn't
            # call super b/c it needs the auto publish above to have happened before any of the create_items
            # in this. The explicit use of SplitMongoModuleStore is intentional
            with self.branch_setting(ModuleStoreEnum.Branch.draft_preferred, item.id):
                # pylint: disable=bad-super-call
                super(SplitMongoModuleStore, self).create_course(
                    org, course, run, user_id, runtime=item.runtime, **kwargs
                )

        return item

    def get_course(self, course_id, depth=0, **kwargs):
        course_id = self._map_revision_to_branch(course_id)
        return super(DraftVersioningModuleStore, self).get_course(course_id, depth=depth, **kwargs)

    def get_courses(self, **kwargs):
        """
        Returns all the courses on the Draft or Published branch depending on the branch setting.
        """
        branch_setting = self.get_branch_setting()
        if branch_setting == ModuleStoreEnum.Branch.draft_preferred:
            return super(DraftVersioningModuleStore, self).get_courses(ModuleStoreEnum.BranchName.draft, **kwargs)
        elif branch_setting == ModuleStoreEnum.Branch.published_only:
            return super(DraftVersioningModuleStore, self).get_courses(ModuleStoreEnum.BranchName.published, **kwargs)
        else:
            raise InsufficientSpecificationError()

    def _auto_publish_no_children(self, location, category, user_id, **kwargs):
        """
        Publishes item if the category is DIRECT_ONLY. This assumes another method has checked that
        location points to the head of the branch and ignores the version. If you call this in any
        other context, you may blow away another user's changes.
        NOTE: only publishes the item at location: no children get published.
        """
        if location.branch == ModuleStoreEnum.BranchName.draft and category in DIRECT_ONLY_CATEGORIES:
            # version_agnostic b/c of above assumption in docstring
            self.publish(location.version_agnostic(), user_id, blacklist=EXCLUDE_ALL, **kwargs)

    def update_item(self, descriptor, user_id, allow_not_found=False, force=False, **kwargs):
        item = super(DraftVersioningModuleStore, self).update_item(
            descriptor,
            user_id,
            allow_not_found=allow_not_found,
            force=force,
            **kwargs
        )
        self._auto_publish_no_children(item.location, item.location.category, user_id, **kwargs)
        return item

    def create_item(
        self, user_id, course_key, block_type, block_id=None,
        definition_locator=None, fields=None,
        force=False, continue_version=False, skip_auto_publish=False, **kwargs
    ):
        """
        See :py:meth `ModuleStoreDraftAndPublished.create_item`
        """
        course_key = self._map_revision_to_branch(course_key)
        item = super(DraftVersioningModuleStore, self).create_item(
            user_id, course_key, block_type, block_id=block_id,
            definition_locator=definition_locator, fields=fields,
            force=force, continue_version=continue_version, **kwargs
        )
        if not skip_auto_publish:
            self._auto_publish_no_children(item.location, item.location.category, user_id, **kwargs)
        return item

    def create_child(
            self, user_id, parent_usage_key, block_type, block_id=None,
            fields=None, continue_version=False, **kwargs
    ):
        parent_usage_key = self._map_revision_to_branch(parent_usage_key)
        item = super(DraftVersioningModuleStore, self).create_child(
            user_id, parent_usage_key, block_type, block_id=block_id,
            fields=fields, continue_version=continue_version, **kwargs
        )
        self._auto_publish_no_children(parent_usage_key, item.location.category, user_id, **kwargs)
        return item

    def delete_item(self, location, user_id, revision=None, **kwargs):
        """
        Delete the given item from persistence. kwargs allow modulestore specific parameters.

        Args:
            location: UsageKey of the item to be deleted
            user_id: id of the user deleting the item
            revision:
                None - deletes the item and its subtree, and updates the parents per description above
                ModuleStoreEnum.RevisionOption.published_only - removes only Published versions
                ModuleStoreEnum.RevisionOption.all - removes both Draft and Published parents
                    currently only provided by contentstore.views.item.orphan_handler
                Otherwise, raises a ValueError.
        """
        if revision == ModuleStoreEnum.RevisionOption.published_only:
            branches_to_delete = [ModuleStoreEnum.BranchName.published]
        elif revision == ModuleStoreEnum.RevisionOption.all:
            branches_to_delete = [ModuleStoreEnum.BranchName.published, ModuleStoreEnum.BranchName.draft]
        elif revision is None:
            branches_to_delete = [ModuleStoreEnum.BranchName.draft]
        else:
            raise UnsupportedRevisionError(
                [
                    None,
                    ModuleStoreEnum.RevisionOption.published_only,
                    ModuleStoreEnum.RevisionOption.all
                ]
            )

        for branch in branches_to_delete:
            branched_location = location.for_branch(branch)
            parent_loc = self.get_parent_location(branched_location)
            SplitMongoModuleStore.delete_item(self, branched_location, user_id)
            self._auto_publish_no_children(parent_loc, parent_loc.category, user_id, **kwargs)

    def _map_revision_to_branch(self, key, revision=None):
        """
        Maps RevisionOptions to BranchNames, inserting them into the key
        """

        if revision == ModuleStoreEnum.RevisionOption.published_only:
            return key.for_branch(ModuleStoreEnum.BranchName.published)
        elif revision == ModuleStoreEnum.RevisionOption.draft_only:
            return key.for_branch(ModuleStoreEnum.BranchName.draft)
        elif revision is None:
            if key.branch is not None:
                return key
            elif self.get_branch_setting(key) == ModuleStoreEnum.Branch.draft_preferred:
                return key.for_branch(ModuleStoreEnum.BranchName.draft)
            else:
                return key.for_branch(ModuleStoreEnum.BranchName.published)
        else:
            raise UnsupportedRevisionError()

    def has_item(self, usage_key, revision=None):
        """
        Returns True if location exists in this ModuleStore.
        """
        usage_key = self._map_revision_to_branch(usage_key, revision=revision)
        return super(DraftVersioningModuleStore, self).has_item(usage_key)

    def get_item(self, usage_key, depth=0, revision=None, **kwargs):
        """
        Returns the item identified by usage_key and revision.
        """
        usage_key = self._map_revision_to_branch(usage_key, revision=revision)
        return super(DraftVersioningModuleStore, self).get_item(usage_key, depth=depth, **kwargs)

    def get_items(self, course_locator, revision=None, **kwargs):
        """
        Returns a list of XModuleDescriptor instances for the matching items within the course with
        the given course_locator.
        """
        course_locator = self._map_revision_to_branch(course_locator, revision=revision)
        return super(DraftVersioningModuleStore, self).get_items(course_locator, **kwargs)

    def get_parent_location(self, location, revision=None, **kwargs):
        '''
        Returns the given location's parent location in this course.
        Args:
            revision:
                None - uses the branch setting for the revision
                ModuleStoreEnum.RevisionOption.published_only
                    - return only the PUBLISHED parent if it exists, else returns None
                ModuleStoreEnum.RevisionOption.draft_preferred
                    - return either the DRAFT or PUBLISHED parent, preferring DRAFT, if parent(s) exists,
                        else returns None
        '''
        if revision == ModuleStoreEnum.RevisionOption.draft_preferred:
            revision = ModuleStoreEnum.RevisionOption.draft_only
        location = self._map_revision_to_branch(location, revision=revision)
        return SplitMongoModuleStore.get_parent_location(self, location, **kwargs)

    def get_orphans(self, course_key, **kwargs):
        course_key = self._map_revision_to_branch(course_key)
        return super(DraftVersioningModuleStore, self).get_orphans(course_key, **kwargs)

    def has_changes(self, xblock):
        """
        Checks if the given block has unpublished changes
        :param xblock: the block to check
        :return: True if the draft and published versions differ
        """
        def get_block(branch_name):
            course_structure = self._lookup_course(xblock.location.for_branch(branch_name))['structure']
            return self._get_block_from_structure(course_structure, xblock.location.block_id)

        draft_block = get_block(ModuleStoreEnum.BranchName.draft)
        published_block = get_block(ModuleStoreEnum.BranchName.published)
        if not published_block:
            return True

        # check if the draft has changed since the published was created
        return self._get_version(draft_block) != self._get_version(published_block)


    def publish(self, location, user_id, blacklist=None, **kwargs):
        """
        Publishes the subtree under location from the draft branch to the published branch
        Returns the newly published item.
        """
        SplitMongoModuleStore.copy(
            self,
            user_id,
            # Directly using the replace function rather than the for_branch function
            # because for_branch obliterates the version_guid and will lead to missed version conflicts.
            location.course_key.replace(branch=ModuleStoreEnum.BranchName.draft),
            location.course_key.for_branch(ModuleStoreEnum.BranchName.published),
            [location],
            blacklist=blacklist
        )
        return self.get_item(location.for_branch(ModuleStoreEnum.BranchName.published), **kwargs)

    def unpublish(self, location, user_id, **kwargs):
        """
        Deletes the published version of the item.
        Returns the newly unpublished item.
        """
        self.delete_item(location, user_id, revision=ModuleStoreEnum.RevisionOption.published_only)
        return self.get_item(location.for_branch(ModuleStoreEnum.BranchName.draft), **kwargs)

    def revert_to_published(self, location, user_id):
        """
        Reverts an item to its last published version (recursively traversing all of its descendants).
        If no published version exists, a VersionConflictError is thrown.

        If a published version exists but there is no draft version of this item or any of its descendants, this
        method is a no-op.

        :raises InvalidVersionError: if no published version exists for the location specified
        """
        raise NotImplementedError()

    def get_course_history_info(self, course_locator):
        """
        See :py:meth `xmodule.modulestore.split_mongo.split.SplitMongoModuleStore.get_course_history_info`
        """
        course_locator = self._map_revision_to_branch(course_locator)
        return super(DraftVersioningModuleStore, self).get_course_history_info(course_locator)

    def get_course_successors(self, course_locator, version_history_depth=1):
        """
        See :py:meth `xmodule.modulestore.split_mongo.split.SplitMongoModuleStore.get_course_successors`
        """
        course_locator = self._map_revision_to_branch(course_locator)
        return super(DraftVersioningModuleStore, self).get_course_successors(
            course_locator, version_history_depth=version_history_depth
        )

    def get_block_generations(self, block_locator):
        """
        See :py:meth `xmodule.modulestore.split_mongo.split.SplitMongoModuleStore.get_block_generations`
        """
        block_locator = self._map_revision_to_branch(block_locator)
        return super(DraftVersioningModuleStore, self).get_block_generations(block_locator)

    def compute_publish_state(self, xblock):
        """
        Returns whether this xblock is draft, public, or private.

        Returns:
            PublishState.draft - published exists and is different from draft
            PublishState.public - published exists and is the same as draft
            PublishState.private - no published version exists
        """
        draft_head = self._get_head(xblock, ModuleStoreEnum.BranchName.draft)
        published_head = self._get_head(xblock, ModuleStoreEnum.BranchName.published)

        if not published_head:
            # published version does not exist
            return PublishState.private
        elif self._get_version(draft_head) == self._get_version(published_head):
            # published and draft versions are equal
            return PublishState.public
        else:
            # published and draft versions differ
            return PublishState.draft

    def convert_to_draft(self, location, user_id):
        """
        Create a copy of the source and mark its revision as draft.

        :param source: the location of the source (its revision must be None)
        """
        # This is a no-op in Split since a draft version of the data always remains
        pass

    def _get_head(self, xblock, branch):
        course_structure = self._lookup_course(xblock.location.course_key.for_branch(branch))['structure']
        return self._get_block_from_structure(course_structure, xblock.location.block_id)

    def _get_version(self, block):
        """
        Return the version of the given database representation of a block.
        """
        return block['edit_info'].get('source_version', block['edit_info']['update_version'])

    def import_xblock(self, user_id, course_key, block_type, block_id, fields=None, runtime=None, **kwargs):
        """
        Split-based modulestores need to import published blocks to both branches
        """
        # hardcode course root block id
        if block_type == 'course':
            block_id = self.DEFAULT_ROOT_BLOCK_ID
        new_usage_key = course_key.make_usage_key(block_type, block_id)

        if self.get_branch_setting() == ModuleStoreEnum.Branch.published_only:
            # if importing a direct only, override existing draft
            if block_type in DIRECT_ONLY_CATEGORIES:
                draft_course = course_key.for_branch(ModuleStoreEnum.BranchName.draft)
                with self.branch_setting(ModuleStoreEnum.Branch.draft_preferred, draft_course):
                    draft = self.import_xblock(user_id, draft_course, block_type, block_id, fields, runtime)
                    self._auto_publish_no_children(draft.location, block_type, user_id)
                return self.get_item(new_usage_key.for_branch(ModuleStoreEnum.BranchName.published))
            # if new to published
            elif not self.has_item(new_usage_key.for_branch(ModuleStoreEnum.BranchName.published)):
                # check whether it's new to draft
                if not self.has_item(new_usage_key.for_branch(ModuleStoreEnum.BranchName.draft)):
                    # add to draft too
                    draft_course = course_key.for_branch(ModuleStoreEnum.BranchName.draft)
                    with self.branch_setting(ModuleStoreEnum.Branch.draft_preferred, draft_course):
                        draft = self.import_xblock(user_id, draft_course, block_type, block_id, fields, runtime)
                        return self.publish(draft.location, user_id, blacklist=EXCLUDE_ALL)

        # do the import
        partitioned_fields = self.partition_fields_by_scope(block_type, fields)
        course_key = self._map_revision_to_branch(course_key)  # cast to branch_setting
        return self._update_item_from_fields(
            user_id, course_key, block_type, block_id, partitioned_fields, None, allow_not_found=True, force=True
        )
