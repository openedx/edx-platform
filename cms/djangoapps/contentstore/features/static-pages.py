#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from selenium.webdriver.common.keys import Keys


@step(u'I go to the static pages page')
def go_to_static(_step):
    menu_css = 'li.nav-course-courseware'
    static_css = 'li.nav-course-courseware-pages'
    world.css_find(menu_css).click()
    world.css_find(static_css).click()


@step(u'I add a new page')
def add_page(_step):
    button_css = 'a.new-button'
    world.css_find(button_css).click()


@step(u'I should( not)? see a "([^"]*)" static page$')
def see_page(_step, doesnt, page):
    index = get_index(page)
    if doesnt:
        assert index == -1
    else:
        assert index != -1


@step(u'I "([^"]*)" the "([^"]*)" page$')
def click_edit_delete(_step, edit_delete, page):
    button_css = 'a.%s-button' % edit_delete
    index = get_index(page)
    assert index != -1
    world.css_find(button_css)[index].click()


@step(u'I change the name to "([^"]*)"$')
def change_name(_step, new_name):
    settings_css = '#settings-mode'
    world.css_find(settings_css).click()
    input_css = 'input.setting-input'
    name_input = world.css_find(input_css)
    old_name = name_input.value
    for count in range(len(old_name)):
        name_input._element.send_keys(Keys.END, Keys.BACK_SPACE)
    name_input._element.send_keys(new_name)
    save_button = 'a.save-button'
    world.css_find(save_button).click()


def get_index(name):
    page_name_css = 'section[data-type="HTMLModule"]'
    all_pages = world.css_find(page_name_css)
    for i in range(len(all_pages)):
        if all_pages[i].html == '\n    {name}\n'.format(name=name):
            return i
    return -1
