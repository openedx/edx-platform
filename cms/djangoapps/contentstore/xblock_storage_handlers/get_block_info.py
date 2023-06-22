"""
Retrieves additional information about a block, including its metadata, data, and id.
"""


from opaque_keys.edx.locator import LibraryUsageLocator
from common.djangoapps.static_replace import replace_static_urls
from xmodule.modulestore.django import (
    modulestore,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.inheritance import (
    own_metadata,
)  # lint-amnesty, pylint: disable=wrong-import-order

from .helpers import (
    add_container_page_publishing_info,
)
from .create_xblock_info import create_xblock_info


def get_block_info(
    xblock,
    rewrite_static_links=True,
    include_ancestor_info=False,
    include_publishing_info=False,
):
    """
    metadata, data, id representation of a leaf block fetcher.
    :param usage_key: A UsageKey
    """
    with modulestore().bulk_operations(xblock.location.course_key):
        data = getattr(xblock, "data", "")
        if rewrite_static_links:
            data = replace_static_urls(data, None, course_id=xblock.location.course_key)

        # Pre-cache has changes for the entire course because we'll need it for the ancestor info
        # Except library blocks which don't [yet] use draft/publish
        if not isinstance(xblock.location, LibraryUsageLocator):
            modulestore().has_changes(
                modulestore().get_course(xblock.location.course_key, depth=None)
            )

        # Note that children aren't being returned until we have a use case.
        xblock_info = create_xblock_info(
            xblock,
            data=data,
            metadata=own_metadata(xblock),
            include_ancestor_info=include_ancestor_info,
        )
        if include_publishing_info:
            add_container_page_publishing_info(xblock, xblock_info)

        return xblock_info
