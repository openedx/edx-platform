"""
Module for the dual-branch fall-back Draft->Published Versioning ModuleStore
"""

from split import SplitMongoModuleStore
from xmodule.modulestore import ModuleStoreEnum


class DraftVersioningModuleStore(SplitMongoModuleStore):
    """
    A subclass of Split that supports a dual-branch fall-back versioning framework
        with a Draft branch that falls back to a Published branch.
    """
    def __init__(self, **kwargs):

        super(DraftVersioningModuleStore, self).__init__()
        self.branch_setting_func = kwargs.pop('branch_setting_func', lambda: ModuleStoreEnum.Branch.published_only)

