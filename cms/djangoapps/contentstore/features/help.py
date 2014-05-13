from lettuce import world, step
from nose.tools import assert_false


def find_online_help_for(page_name):
    return world.browser.find_by_xpath(
        '//li[contains(@class, "nav-account-help")]//a[contains(@href, "{page_name}")]'.format(
            page_name=page_name
        )
    )


@step(u'I should see online help for "([^"]*)"$')
def see_online_help_for(step, page_name):
    elements_found = find_online_help_for(page_name)
    assert_false(elements_found.is_empty())

