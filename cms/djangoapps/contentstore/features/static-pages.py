#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from selenium.webdriver.common.keys import Keys
from nose.tools import assert_true # pylint: disable=E0611


@step(u'I go to the static pages page')
def go_to_static(_step):
    menu_css = 'li.nav-course-courseware'
    static_css = 'li.nav-course-courseware-pages a'
    world.css_click(menu_css)
    world.css_click(static_css)


@step(u'I add a new page')
def add_page(_step):
    button_css = 'a.new-button'
    world.css_click(button_css)


@step(u'I should( not)? see a "([^"]*)" static page$')
def see_page(_step, doesnt, page):

    should_exist = not doesnt

    # Need to retry here because the element
    # will sometimes exist before the HTML content is loaded
    exists_func = lambda(driver): page_exists(page) == should_exist
    world.wait_for(exists_func)
    assert_true(exists_func(None))


@step(u'I "([^"]*)" the "([^"]*)" page$')
def click_edit_delete(_step, edit_delete, page):
    button_css = 'a.%s-button' % edit_delete
    index = get_index(page)
    assert index is not None
    world.css_click(button_css, index=index)


@step(u'I change the name to "([^"]*)"$')
def change_name(_step, new_name):
    settings_css = '#settings-mode a'
    world.css_click(settings_css)
    input_css = 'input.setting-input'
    world.css_fill(input_css, new_name)
    if world.is_firefox():
        world.trigger_event(input_css)
    save_button = 'a.save-button'
    world.css_click(save_button)


def get_index(name):
    page_name_css = 'section[data-type="HTMLModule"]'
    all_pages = world.css_find(page_name_css)
    for i in range(len(all_pages)):
        if world.css_html(page_name_css, index=i) == '\n    {name}\n'.format(name=name):
            return i
    return None

def page_exists(page):
    return get_index(page) is not None
