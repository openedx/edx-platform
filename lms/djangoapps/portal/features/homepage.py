from lettuce import world, step

@step('I should see "([^"]*)" in the Partners section$')
def i_should_see_partner(step, partner):
    assert (partner in world.browser.find_by_css(".partners").text)
