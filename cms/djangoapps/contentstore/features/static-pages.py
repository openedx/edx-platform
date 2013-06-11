#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from selenium.webdriver.common.keys import Keys


@step(u'I go to the static pages page')
def go_to_uploads(step):
    menu_css = 'li.nav-course-courseware'
    uploads_css = '.nav-course-courseware-pages'
    world.css_find(menu_css).click()
    world.css_find(uploads_css).click()


@step(u'I add a new page')
def add_page(step):
    button_css = '.new-button'
    world.css_find(button_css).click()


@step(u'I should( not)? see a "([^"]*)" static page$')
def see_page(step, doesnt, page):
    index = get_index(page)
    if doesnt:
        assert index == -1
    else:
        assert index != -1


@step(u'I "([^"]*)" the "([^"]*)" page$')
def click_edit_delete(step, edit_delete, page):
    button_css = '.%s-button' % edit_delete
    index = get_index(page)
    assert index != -1
    world.css_find(button_css)[index].click()


@step(u'I change the name to "([^"]*)"$')
def change_name(step, new_name):
    settings_css = '#settings-mode'
    world.css_find(settings_css).click()
    input_css = '.setting-input'
    name_input = world.css_find(input_css)
    old_name = name_input.value
    for count in range(len(old_name)):
        name_input._element.send_keys(Keys.END, Keys.BACK_SPACE)
    name_input._element.send_keys(new_name)
    save_button = '.save-button'
    world.css_find(save_button).click()


@step(u'I move "([^"]*)" after "([^"]*)"$')
def change_list(step, item1, item2):
    index1 = get_index(item1)
    index2 = get_index(item2)
    assert index1 != -1 and index2 != -1
    world.drag_sortable_after(".component", index1, index2, ".ui-sortable")


@step(u'I see the order is "([^"]*)"$')
def check_order(step, items):
    items = items.split(' ')
    name_css = 'section[data-type="HTMLModule"]'
    all_elements = world.css_find(name_css)
    for i in range(len(items)):
        assert all_elements[i].html == '\n    %s\n' % items[i]


def get_index(name):
    page_name_css = 'section[data-type="HTMLModule"]'
    all_pages = world.css_find(page_name_css)
    for i in range(len(all_pages)):
        if all_pages[i].html == '\n    %s\n' % name:
            return i
    return -1
