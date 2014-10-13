"""
This module provides an abstraction for Module Stores that support Draft and Published branches.
"""

import threading
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from . import ModuleStoreEnum

# Things w/ these categories should never be marked as version=DRAFT
DIRECT_ONLY_CATEGORIES = ['course', 'chapter', 'sequential', 'about', 'static_tab', 'course_info']


class BranchSettingMixin(object):
    """
    A mixin to manage a module store's branch setting.
    The order of override is (from higher precedence to lower):
       1. thread-specific setting temporarily set using the branch_setting contextmanager
       2. the return value of the branch_setting_func passed into this mixin's init method
       3. the default branch setting being ModuleStoreEnum.Branch.published_only
    """

    def __init__(self, *args, **kwargs):
        """
        :param branch_setting_func: a function that returns the default branch setting for this object.
            If not specified, ModuleStoreEnum.Branch.published_only is used as the default setting.
        """
        super(BranchSettingMixin, self).__init__(*args, **kwargs)
        self.default_branch_setting_func = kwargs.pop(
            'branch_setting_func',
            lambda: ModuleStoreEnum.Branch.published_only
        )

        # cache the branch setting on a local thread to support a multi-threaded environment
        self.thread_cache = threading.local()

    @contextmanager
    def branch_setting(self, branch_setting, course_id=None):  # pylint: disable=unused-argument
        """
        A context manager for temporarily setting a store's branch value on the current thread.
        """
        previous_thread_branch_setting = getattr(self.thread_cache, 'branch_setting', None)
        try:
            self.thread_cache.branch_setting = branch_setting
            yield
        finally:
            self.thread_cache.branch_setting = previous_thread_branch_setting

    def get_branch_setting(self, course_id=None):  # pylint: disable=unused-argument
        """
        Returns the current branch_setting on the store.

        Returns the thread-local setting, if set.
        Otherwise, returns the default value of the setting function set during the store's initialization.
        """
        # first check the thread-local cache
        thread_local_branch_setting = getattr(self.thread_cache, 'branch_setting', None)
        if thread_local_branch_setting:
            return thread_local_branch_setting
        else:
            # return the default value
            return self.default_branch_setting_func()


class ModuleStoreDraftAndPublished(BranchSettingMixin):
    """
    A mixin for a read-write database backend that supports two branches, Draft and Published, with
    options to prefer Draft and fallback to Published.
    """
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        super(ModuleStoreDraftAndPublished, self).__init__(*args, **kwargs)

    @abstractmethod
    def delete_item(self, location, user_id, revision=None, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def get_parent_location(self, location, revision=None, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def has_changes(self, xblock):
        raise NotImplementedError

    @abstractmethod
    def publish(self, location, user_id):
        raise NotImplementedError

    @abstractmethod
    def unpublish(self, location, user_id):
        raise NotImplementedError

    @abstractmethod
    def revert_to_published(self, location, user_id):
        raise NotImplementedError

    @abstractmethod
    def has_published_version(self, xblock):
        raise NotImplementedError

    @abstractmethod
    def convert_to_draft(self, location, user_id):
        raise NotImplementedError

    @abstractmethod
    def import_xblock(self, user_id, course_key, block_type, block_id, fields=None, runtime=None, **kwargs):
        """
        Import the given xblock into the current branch setting: import completely overwrites any
        existing block of the same id.

        In ModuleStoreDraftAndPublished, importing a published block ensures that access from the draft
        will get a block (either the one imported or a preexisting one). See xml_importer
        """
        raise NotImplementedError


class   UnsupportedRevisionError(ValueError):
    """
    This error is raised if a method is called with an unsupported revision parameter.
    """
    def __init__(self, allowed_revisions=None):
        if not allowed_revisions:
            allowed_revisions = [
                None,
                ModuleStoreEnum.RevisionOption.published_only,
                ModuleStoreEnum.RevisionOption.draft_only
            ]
        super(UnsupportedRevisionError, self).__init__('revision not one of {}'.format(allowed_revisions))
