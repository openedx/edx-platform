#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world
from nose.tools import assert_equal

import time


@world.absorb
def create_component_instance(step, component_button_css, instance_id, expected_css):
    click_new_component_button(step, component_button_css)
    click_component_from_menu(instance_id, expected_css)


@world.absorb
def click_new_component_button(step, component_button_css):
    step.given('I have opened a new course section in Studio')
    step.given('I have added a new subsection')
    step.given('I expand the first section')
    world.css_click('a.new-unit-item')
    world.css_click(component_button_css)


@world.absorb
def click_component_from_menu(instance_id, expected_css):
    new_instance = world.browser.find_by_id(instance_id)
    assert_equal(1, len(new_instance))
    # TODO: why is this sleep necessary?
    time.sleep(float(1))
    new_instance[0].click()
    assert_equal(1, len(world.css_find(expected_css)))
