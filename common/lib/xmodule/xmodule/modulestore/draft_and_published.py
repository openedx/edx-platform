"""
This module provides an abstraction for Module Stores that support Draft and Published branches.
"""

from abc import ABCMeta, abstractmethod
from . import ModuleStoreEnum

class ModuleStoreDraftAndPublished(object):
    """
    A mixin for a read-write database backend that supports two branches, Draft and Published, with
    options to prefer Draft and fallback to Published.
    """
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        super(ModuleStoreDraftAndPublished, self).__init__(*args, **kwargs)
        self.branch_setting_func = kwargs.pop('branch_setting_func', lambda: ModuleStoreEnum.Branch.published_only)

    @abstractmethod
    def delete_item(self, location, user_id, revision=None, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def get_parent_location(self, location, revision=None, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def has_changes(self, usage_key):
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
    def compute_publish_state(self, xblock):
        raise NotImplementedError

    @abstractmethod
    def convert_to_draft(self, location, user_id):
        raise NotImplementedError
