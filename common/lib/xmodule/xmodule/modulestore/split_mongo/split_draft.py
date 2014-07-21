"""
Module for the dual-branch fall-back Draft->Published Versioning ModuleStore
"""

from ..exceptions import ItemNotFoundError
from split import SplitMongoModuleStore, EXCLUDE_ALL
from xmodule.modulestore import ModuleStoreEnum, PublishState
from xmodule.modulestore.exceptions import InsufficientSpecificationError
from xmodule.modulestore.draft_and_published import ModuleStoreDraftAndPublished, DIRECT_ONLY_CATEGORIES, UnsupportedRevisionError


class DraftVersioningModuleStore(ModuleStoreDraftAndPublished, SplitMongoModuleStore):
    """
    A subclass of Split that supports a dual-branch fall-back versioning framework
        with a Draft branch that falls back to a Published branch.
    """
    def _lookup_course(self, course_locator):
        """
        overrides the implementation of _lookup_course in SplitMongoModuleStore in order to
        use the configured branch_setting in the course_locator
        """
        if course_locator.org and course_locator.course and course_locator.run:
            if course_locator.branch is None:
                # default it based on branch_setting
                branch_setting = self.get_branch_setting()
                if branch_setting == ModuleStoreEnum.Branch.draft_preferred:
                    course_locator = course_locator.for_branch(ModuleStoreEnum.BranchName.draft)
                elif branch_setting == ModuleStoreEnum.Branch.published_only:
                    course_locator = course_locator.for_branch(ModuleStoreEnum.BranchName.published)
                else:
                    raise InsufficientSpecificationError(course_locator)
        return super(DraftVersioningModuleStore, self)._lookup_course(course_locator)

    def create_course(self, org, course, run, user_id, **kwargs):
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
        self._auto_publish_no_children(item.location, item.location.category, user_id)
        return item

    def get_courses(self):
        """
        Returns all the courses on the Draft branch (which is a superset of the courses on the Published branch).
        """
        return super(DraftVersioningModuleStore, self).get_courses(ModuleStoreEnum.BranchName.draft)

    def _auto_publish_no_children(self, location, category, user_id):
        """
        Publishes item if the category is DIRECT_ONLY. This assumes another method has checked that
        location points to the head of the branch and ignores the version. If you call this in any
        other context, you may blow away another user's changes.
        NOTE: only publishes the item at location: no children get published.
        """
        if location.branch == ModuleStoreEnum.BranchName.draft and category in DIRECT_ONLY_CATEGORIES:
            # version_agnostic b/c of above assumption in docstring
            self.publish(location.version_agnostic(), user_id, blacklist=EXCLUDE_ALL)

    def update_item(self, descriptor, user_id, allow_not_found=False, force=False):
        item = super(DraftVersioningModuleStore, self).update_item(
            descriptor,
            user_id,
            allow_not_found=allow_not_found,
            force=force
        )
        self._auto_publish_no_children(item.location, item.location.category, user_id)
        return item

    def create_item(
        self, user_id, course_key, block_type, block_id=None,
        definition_locator=None, fields=None,
        force=False, continue_version=False, **kwargs
    ):
        item = super(DraftVersioningModuleStore, self).create_item(
            user_id, course_key, block_type, block_id=block_id,
            definition_locator=definition_locator, fields=fields,
            force=force, continue_version=continue_version, **kwargs
        )
        self._auto_publish_no_children(item.location, item.location.category, user_id)
        return item

    def create_child(
            self, user_id, parent_usage_key, block_type, block_id=None,
            fields=None, continue_version=False, **kwargs
    ):
        item = super(DraftVersioningModuleStore, self).create_child(
            user_id, parent_usage_key, block_type, block_id=block_id,
            fields=fields, continue_version=continue_version, **kwargs
        )
        self._auto_publish_no_children(parent_usage_key, item.location.category, user_id)
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
            SplitMongoModuleStore.delete_item(self, branched_location, user_id, **kwargs)
            self._auto_publish_no_children(parent_loc, parent_loc.category, user_id)

    def _map_revision_to_branch(self, key, revision=None):
        """
        Maps RevisionOptions to BranchNames, inserting them into the key
        """
        if revision == ModuleStoreEnum.RevisionOption.published_only:
            return key.for_branch(ModuleStoreEnum.BranchName.published)
        elif revision == ModuleStoreEnum.RevisionOption.draft_only:
            return key.for_branch(ModuleStoreEnum.BranchName.draft)
        elif revision is None:
            return key
        else:
            raise UnsupportedRevisionError()

    def has_item(self, usage_key, revision=None):
        """
        Returns True if location exists in this ModuleStore.
        """
        usage_key = self._map_revision_to_branch(usage_key, revision=revision)
        return super(DraftVersioningModuleStore, self).has_item(usage_key)

    def get_item(self, usage_key, depth=0, revision=None):
        """
        Returns the item identified by usage_key and revision.
        """
        usage_key = self._map_revision_to_branch(usage_key, revision=revision)
        return super(DraftVersioningModuleStore, self).get_item(usage_key, depth=depth)

    def get_items(self, course_locator, settings=None, content=None, revision=None, **kwargs):
        """
        Returns a list of XModuleDescriptor instances for the matching items within the course with
        the given course_locator.
        """
        course_locator = self._map_revision_to_branch(course_locator, revision=revision)
        return super(DraftVersioningModuleStore, self).get_items(
            course_locator,
            settings=settings,
            content=content,
            **kwargs
        )

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

    def has_changes(self, usage_key):
        """
        Checks if the given block has unpublished changes
        :param usage_key: the block to check
        :return: True if the draft and published versions differ
        """
        # TODO for better performance: lookup the courses and get the block entry, don't create the instances
        draft = self.get_item(usage_key.for_branch(ModuleStoreEnum.BranchName.draft))
        try:
            published = self.get_item(usage_key.for_branch(ModuleStoreEnum.BranchName.published))
        except ItemNotFoundError:
            return True

        return draft.update_version != published.source_version

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
        return self.get_item(location.for_branch(ModuleStoreEnum.BranchName.published))

    def unpublish(self, location, user_id):
        """
        Deletes the published version of the item.
        Returns the newly unpublished item.
        """
        self.delete_item(location, user_id, revision=ModuleStoreEnum.RevisionOption.published_only)
        return self.get_item(location.for_branch(ModuleStoreEnum.BranchName.draft))

    def revert_to_published(self, location, user_id):
        """
        Reverts an item to its last published version (recursively traversing all of its descendants).
        If no published version exists, a VersionConflictError is thrown.

        If a published version exists but there is no draft version of this item or any of its descendants, this
        method is a no-op.

        :raises InvalidVersionError: if no published version exists for the location specified
        """
        raise NotImplementedError()

    def compute_publish_state(self, xblock):
        """
        Returns whether this xblock is draft, public, or private.

        Returns:
            PublishState.draft - published exists and is different from draft
            PublishState.public - published exists and is the same as draft
            PublishState.private - no published version exists
        """
        def get_head(branch):
            course_structure = self._lookup_course(xblock.location.course_key.for_branch(branch))['structure']
            return self._get_block_from_structure(course_structure, xblock.location.block_id)

        def get_version(block):
            """
            Return the version of the given database representation of a block.
            """
            #TODO: make this method a more generic helper
            return block['edit_info'].get('source_version', block['edit_info']['update_version'])

        draft_head = get_head(ModuleStoreEnum.BranchName.draft)
        published_head = get_head(ModuleStoreEnum.BranchName.published)

        if not published_head:
            # published version does not exist
            return PublishState.private
        elif get_version(draft_head) == get_version(published_head):
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
