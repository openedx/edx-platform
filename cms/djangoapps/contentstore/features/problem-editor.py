#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from nose.tools import assert_true, assert_equal, assert_in
from terrain.steps import reload_the_page
from selenium.common.exceptions import StaleElementReferenceException
import time


############### ACTIONS ####################
@step('I have created a Blank Common Problem$')
def i_created_blank_common_problem(step):
    step.given('I have opened a new course section in Studio')
    step.given('I have added a new subsection')
    step.given('I expand the first section')
    world.css_click('a.new-unit-item')
    time.sleep(float(2))
#    world.css_click('a.problem')
