# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

from lettuce import world
from cms.djangoapps.contentstore.features.common import press_the_notification_button, type_in_codemirror

KEY_CSS = '.key h3.title'
ADVANCED_MODULES_KEY = "Advanced Module List"


def get_index_of(expected_key):
    for i, element in enumerate(world.css_find(KEY_CSS)):
        # Sometimes get stale reference if I hold on to the array of elements
        key = world.css_value(KEY_CSS, index=i)
        if key == expected_key:
            return i

    return -1


def change_value(step, key, new_value):
    index = get_index_of(key)
    type_in_codemirror(index, new_value)
    press_the_notification_button(step, "Save")
    world.wait_for_ajax_complete()
