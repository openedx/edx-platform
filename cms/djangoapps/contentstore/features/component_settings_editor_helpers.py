# disable missing docstring
#pylint: disable=C0111

from lettuce import world
from nose.tools import assert_equal
from terrain.steps import reload_the_page


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
    elem_css = "a[data-location='%s']" % instance_id
    assert_equal(1, len(world.css_find(elem_css)))
    world.css_click(elem_css)
    assert_equal(1, len(world.css_find(expected_css)))
