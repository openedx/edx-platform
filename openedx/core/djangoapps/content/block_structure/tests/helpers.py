"""
Helpers for Course Blocks tests.
"""
from openedx.core.djangolib.testing.waffle_utils import override_switch
from openedx.core.lib.block_structure.exceptions import BlockStructureNotFound
from openedx.core.lib.block_structure.store import BlockStructureStore

from ..api import get_cache
from ..config import _bs_waffle_switch_name


def is_course_in_block_structure_cache(course_key, store):
    """
    Returns whether the given course is in the Block Structure cache.
    """
    course_usage_key = store.make_course_usage_key(course_key)
    try:
        BlockStructureStore(get_cache()).get(course_usage_key)
        return True
    except BlockStructureNotFound:
        return False


class override_config_setting(override_switch):  # pylint:disable=invalid-name
    """
    Subclasses override_switch to use the block structure
    name-spaced switch names.
    """
    def __init__(self, name, active):
        super(override_config_setting, self).__init__(
            _bs_waffle_switch_name(name),
            active
        )
