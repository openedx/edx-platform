from lettuce import world, step
from nose.tools import assert_in

@step('I should see "([^"]*)" in the Partners section$')
def i_should_see_partner(step, partner):
    partners = world.browser.find_by_css(".partner .name span")
    names = set(span.text for span in partners)
    assert_in(partner, names)
