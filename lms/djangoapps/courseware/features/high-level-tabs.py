from lettuce import world, step
from nose.tools import assert_equals


@step(u'I click on the tabs then the page title should contain the following titles:')
def i_click_on_the_tab_and_check(step):
    for tab_title in step.hashes:
        tab_text = tab_title['TabName']
        title = tab_title['PageTitle']
        world.click_link(tab_text)
        world.wait_for(lambda _driver:title in world.browser.title)
        assert(title in world.browser.title)
