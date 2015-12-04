# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

from lettuce import world, step
from nose.tools import assert_equal, assert_in  # pylint: disable=no-name-in-module


CSS_FOR_TAB_ELEMENT = "li[data-tab-id='{0}'] input.toggle-checkbox"


@step(u'I go to the pages page$')
def go_to_static(step):
    menu_css = 'li.nav-course-courseware'
    static_css = 'li.nav-course-courseware-pages a'
    world.css_click(menu_css)
    world.css_click(static_css)


@step(u'I add a new static page$')
def add_page(step):
    button_css = 'a.new-button'
    world.css_click(button_css)


@step(u'I should see a static page named "([^"]*)"$')
def see_a_static_page_named_foo(step, name):
    pages_css = 'div.xmodule_StaticTabModule'
    page_name_html = world.css_html(pages_css)
    assert_equal(page_name_html.strip(), name)


@step(u'I should not see any static pages$')
def not_see_any_static_pages(step):
    pages_css = 'div.xmodule_StaticTabModule'
    assert world.is_css_not_present(pages_css, wait_time=30)


@step(u'I "(edit|delete)" the static page$')
def click_edit_or_delete(step, edit_or_delete):
    button_css = 'ul.component-actions a.%s-button' % edit_or_delete
    world.css_click(button_css)


@step(u'I change the name to "([^"]*)"$')
def change_name(step, new_name):
    settings_css = '.settings-button'
    world.css_click(settings_css)
    input_css = 'input.setting-input'
    world.css_fill(input_css, new_name)
    if world.is_firefox():
        world.trigger_event(input_css)
    world.save_component()


@step(u'I drag the first static page to the last$')
def drag_first_static_page_to_last(step):
    drag_first_to_last_with_css('.component')


@step(u'I have created a static page$')
def create_static_page(step):
    step.given('I have opened the pages page in a new course')
    step.given('I add a new static page')


@step(u'I have opened the pages page in a new course$')
def open_pages_page_in_new_course(step):
    step.given('I have opened a new course in Studio')
    step.given('I go to the pages page')


@step(u'I have created two different static pages$')
def create_two_pages(step):
    step.given('I have created a static page')
    step.given('I "edit" the static page')
    step.given('I change the name to "First"')
    step.given('I add a new static page')
    # Verify order of pages
    _verify_page_names('First', 'Empty')


@step(u'the static pages are switched$')
def static_pages_are_switched(step):
    _verify_page_names('Empty', 'First')


def _verify_page_names(first, second):
    world.wait_for(
        func=lambda _: len(world.css_find('.xmodule_StaticTabModule')) == 2,
        timeout=200,
        timeout_msg="Timed out waiting for two pages to be present"
    )
    pages = world.css_find('.xmodule_StaticTabModule')
    assert_equal(pages[0].text, first)
    assert_equal(pages[1].text, second)


@step(u'the built-in pages are in the default order$')
def built_in_pages_in_default_order(step):
    expected_pages = ['Courseware', 'Course Info', 'Wiki', 'Progress']
    see_pages_in_expected_order(expected_pages)


@step(u'the built-in pages are switched$')
def built_in_pages_switched(step):
    expected_pages = ['Courseware', 'Course Info', 'Progress', 'Wiki']
    see_pages_in_expected_order(expected_pages)


@step(u'the pages are in the default order$')
def pages_in_default_order(step):
    expected_pages = ['Courseware', 'Course Info', 'Wiki', 'Progress', 'First', 'Empty']
    see_pages_in_expected_order(expected_pages)


@step(u'the pages are switched$$')
def pages_are_switched(step):
    expected_pages = ['Courseware', 'Course Info', 'Progress', 'First', 'Empty', 'Wiki']
    see_pages_in_expected_order(expected_pages)


@step(u'I drag the first page to the last$')
def drag_first_page_to_last(step):
    drag_first_to_last_with_css('.is-movable')


@step(u'I should see the "([^"]*)" page as "(visible|hidden)"$')
def page_is_visible_or_hidden(step, page_id, visible_or_hidden):
    hidden = visible_or_hidden == "hidden"
    assert_equal(world.css_find(CSS_FOR_TAB_ELEMENT.format(page_id)).checked, hidden)


@step(u'I toggle the visibility of the "([^"]*)" page$')
def page_toggle_visibility(step, page_id):
    world.css_find(CSS_FOR_TAB_ELEMENT.format(page_id))[0].click()


def drag_first_to_last_with_css(css_class):
    # For some reason, the drag_and_drop method did not work in this case.
    draggables = world.css_find(css_class + ' .drag-handle')
    source = draggables.first
    target = draggables.last
    source.action_chains.click_and_hold(source._element).perform()  # pylint: disable=protected-access
    source.action_chains.move_to_element_with_offset(target._element, 0, 50).perform()  # pylint: disable=protected-access
    source.action_chains.release().perform()


def see_pages_in_expected_order(page_names_in_expected_order):
    pages = world.css_find("li.course-tab")
    assert_equal(len(page_names_in_expected_order), len(pages))
    for i, page_name in enumerate(page_names_in_expected_order):
        assert_in(page_name, pages[i].text)
