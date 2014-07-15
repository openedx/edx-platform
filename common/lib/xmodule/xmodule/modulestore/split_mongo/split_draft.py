"""
Module for the dual-branch fall-back Draft->Published Versioning ModuleStore
"""

from ..exceptions import ItemNotFoundError
from split import SplitMongoModuleStore
from xmodule.modulestore import ModuleStoreEnum, PublishState
from xmodule.modulestore.draft_and_published import ModuleStoreDraftAndPublished


class DraftVersioningModuleStore(ModuleStoreDraftAndPublished, SplitMongoModuleStore):
    """
    A subclass of Split that supports a dual-branch fall-back versioning framework
        with a Draft branch that falls back to a Published branch.
    """
    def __init__(self, **kwargs):
        super(DraftVersioningModuleStore, self).__init__(**kwargs)

    def create_course(self, org, course, run, user_id, **kwargs):
        master_branch = kwargs.pop('master_branch', ModuleStoreEnum.BranchName.draft)
        return super(DraftVersioningModuleStore, self).create_course(
            org, course, run, user_id, master_branch, **kwargs
        )

    def get_courses(self):
        """
        Returns all the courses on the Draft branch (which is a superset of the courses on the Published branch).
        """
        return super(DraftVersioningModuleStore, self).get_courses(ModuleStoreEnum.BranchName.draft)

    def delete_item(self, location, user_id, revision=None, **kwargs):
        """
        Delete the given item from persistence. kwargs allow modulestore specific parameters.
        """
        if revision == ModuleStoreEnum.RevisionOption.published_only:
            branches_to_delete = [ModuleStoreEnum.BranchName.published]
        elif revision == ModuleStoreEnum.RevisionOption.all:
            branches_to_delete = [ModuleStoreEnum.BranchName.published, ModuleStoreEnum.BranchName.draft]
        else:
            branches_to_delete = [ModuleStoreEnum.BranchName.draft]
        for branch in branches_to_delete:
            SplitMongoModuleStore.delete_item(self, location.for_branch(branch), user_id, **kwargs)

    def _map_revision_to_branch(self, key, revision=None):
        """
        Maps RevisionOptions to BranchNames, inserting them into the key
        """
        def for_branch(branch_state):
            if key.branch is not None and key.branch is not branch_state:
                raise ValueError('{} already has a branch.'.format(key))
            return key.for_branch(branch_state)
        if revision == ModuleStoreEnum.RevisionOption.published_only:
            return for_branch(ModuleStoreEnum.BranchName.published)
        elif revision == ModuleStoreEnum.RevisionOption.draft_only:
            return for_branch(ModuleStoreEnum.BranchName.draft)
        else:
            return key

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
        Returns a list of XModuleDescriptor instances for th matching items within the course with
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
        # NAATODO - support draft_preferred
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
        draft = self.get_item(usage_key.for_branch(ModuleStoreEnum.BranchName.draft))
        try:
            published = self.get_item(usage_key.for_branch(ModuleStoreEnum.BranchName.published))
        except ItemNotFoundError:
            return True

        return draft.update_version != published.update_version

    def publish(self, location, user_id, **kwargs):
        """
        Save a current draft to the underlying modulestore.
        Returns the newly published item.
        """
        SplitMongoModuleStore.copy(
            self,
            user_id,
            location.course_key.for_branch(ModuleStoreEnum.BranchName.draft),
            location.course_key.for_branch(ModuleStoreEnum.BranchName.published),
            [location],
        )

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
        # TODO figure out what to say if xblock is not from the HEAD of its branch
        def get_head(branch):
            course_structure = self._lookup_course(xblock.location.course_key.for_branch(branch))['structure']
            return self._get_block_from_structure(course_structure, xblock.location.block_id)

        if xblock.location.branch is None:
            raise ValueError(u'{} is not in a branch; so, this is nonsensical'.format(xblock.location))
        if xblock.location.branch == ModuleStoreEnum.BranchName.draft:
            other = get_head(ModuleStoreEnum.BranchName.published)
        elif xblock.location.branch == ModuleStoreEnum.BranchName.published:
            other = get_head(ModuleStoreEnum.BranchName.draft)
        else:
            raise ValueError(u'{} is not in a branch other than draft or published; so, this is nonsensical'.format(xblock.location))

        if not other:
            if xblock.location.branch == ModuleStoreEnum.BranchName.draft:
                return PublishState.private
            else:
                return PublishState.public  # a bit nonsensical
        elif xblock.update_version != other['edit_info']['update_version']:
            return PublishState.draft
        else:
            return PublishState.public

    def convert_to_draft(self, location, user_id):
        """
        Create a copy of the source and mark its revision as draft.

        :param source: the location of the source (its revision must be None)
        """
        # This is a no-op in Split since a draft version of the data always remains
        pass
