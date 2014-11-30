# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

from nose.tools import assert_false  # pylint: disable=no-name-in-module
from lettuce import step, world


@step(u'I should see online help for "([^"]*)"$')
def see_online_help_for(step, page_name):
    # make sure the online Help link exists on this page and contains the expected page name
    elements_found = world.browser.find_by_xpath(
        '//li[contains(@class, "nav-account-help")]//a[contains(@href, "{page_name}")]'.format(
            page_name=page_name
        )
    )
    assert_false(elements_found.is_empty())

    # make sure the PDF link on the sock of this page exists
    # for now, the PDF link stays constant for all the pages so we just check for "pdf"
    elements_found = world.browser.find_by_xpath(
        '//section[contains(@class, "sock")]//li[contains(@class, "js-help-pdf")]//a[contains(@href, "pdf")]'
    )
    assert_false(elements_found.is_empty())
