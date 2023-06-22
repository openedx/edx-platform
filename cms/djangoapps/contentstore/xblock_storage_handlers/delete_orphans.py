"""
    Helper function to delete orphans for a given course.
"""
from xmodule.modulestore import (
    ModuleStoreEnum,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.django import (
    modulestore,
)  # lint-amnesty, pylint: disable=wrong-import-order


def delete_orphans(course_usage_key, user_id, commit=False):
    """
    Helper function to delete orphans for a given course.
    If `commit` is False, this function does not actually remove
    the orphans.
    """
    store = modulestore()
    blocks = store.get_orphans(course_usage_key)
    branch = course_usage_key.branch
    if commit:
        with store.bulk_operations(course_usage_key):
            for blockloc in blocks:
                revision = ModuleStoreEnum.RevisionOption.all
                # specify branches when deleting orphans
                if branch == ModuleStoreEnum.BranchName.published:
                    revision = ModuleStoreEnum.RevisionOption.published_only
                store.delete_item(blockloc, user_id, revision=revision)
    return [str(block) for block in blocks]
