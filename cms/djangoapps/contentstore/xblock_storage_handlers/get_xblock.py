import logging

from xmodule.modulestore.exceptions import (
    InvalidLocationError,
    ItemNotFoundError,
)  # lint-amnesty, pylint: disable=wrong-import-order

from xmodule.modulestore.django import (
    modulestore,
)  # lint-amnesty, pylint: disable=wrong-import-order

from common.djangoapps.util.json_request import JsonResponse

log = logging.getLogger(__name__)


def get_xblock(usage_key, user):
    """
    Returns the xblock for the specified usage key. Note: if failing to find a key with a category
    in the CREATE_IF_NOT_FOUND list, an xblock will be created and saved automatically.
    """
    store = modulestore()
    with store.bulk_operations(usage_key.course_key):
        try:
            return store.get_item(usage_key, depth=None)
        except ItemNotFoundError:
            if usage_key.block_type in CREATE_IF_NOT_FOUND:
                # Create a new one for certain categories only. Used for course info handouts.
                return store.create_item(
                    user.id,
                    usage_key.course_key,
                    usage_key.block_type,
                    block_id=usage_key.block_id,
                )
            else:
                raise
        except InvalidLocationError:
            log.error("Can't find item by location.")
            return JsonResponse(
                {"error": "Can't find item by location: " + str(usage_key)}, 404
            )
