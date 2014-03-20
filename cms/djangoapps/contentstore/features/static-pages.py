# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world, step
from nose.tools import assert_equal  # pylint: disable=E0611


@step(u'I go to the static pages page$')
def go_to_static(step):
    menu_css = 'li.nav-course-courseware'
    static_css = 'li.nav-course-courseware-pages a'
    world.css_click(menu_css)
    world.css_click(static_css)


@step(u'I add a new page$')
def add_page(step):
    button_css = 'a.new-button'
    world.css_click(button_css)


@step(u'I should see a static page named "([^"]*)"$')
def see_a_static_page_named_foo(step, name):
    pages_css = 'div.xmodule_StaticTabModule'
    page_name_html = world.css_html(pages_css)
    assert_equal(page_name_html, '\n    {name}\n'.format(name=name))


@step(u'I should not see any static pages$')
def not_see_any_static_pages(step):
    pages_css = 'div.xmodule_StaticTabModule'
    assert (world.is_css_not_present(pages_css, wait_time=30))


@step(u'I "(edit|delete)" the static page$')
def click_edit_or_delete(step, edit_or_delete):
    button_css = 'ul.component-actions a.%s-button' % edit_or_delete
    world.css_click(button_css)


@step(u'I change the name to "([^"]*)"$')
def change_name(step, new_name):
    settings_css = '#settings-mode a'
    world.css_click(settings_css)
    input_css = 'input.setting-input'
    world.css_fill(input_css, new_name)
    if world.is_firefox():
        world.trigger_event(input_css)
    save_button = 'a.save-button'
    world.css_click(save_button)


@step(u'I reorder the tabs')
def reorder_tabs(_step):
    # For some reason, the drag_and_drop method did not work in this case.
    draggables = world.css_find('.drag-handle')
    source = draggables.first
    target = draggables.last
    source.action_chains.click_and_hold(source._element).perform()
    source.action_chains.move_to_element_with_offset(target._element, 0, 50).perform()
    source.action_chains.release().perform()


@step(u'I have created a static page')
def create_static_page(step):
    step.given('I have opened a new course in Studio')
    step.given('I go to the static pages page')
    step.given('I add a new page')


@step(u'I have created two different static pages')
def create_two_pages(step):
    step.given('I have created a static page')
    step.given('I "edit" the static page')
    step.given('I change the name to "First"')
    step.given('I add a new page')
    # Verify order of tabs
    _verify_tab_names('First', 'Empty')


@step(u'the tabs are in the reverse order')
def tabs_in_reverse_order(step):
    _verify_tab_names('Empty', 'First')


def _verify_tab_names(first, second):
    world.wait_for(
        func=lambda _: len(world.css_find('.xmodule_StaticTabModule')) == 2,
        timeout=200,
        timeout_msg="Timed out waiting for two tabs to be present"
    )
    tabs = world.css_find('.xmodule_StaticTabModule')
    assert tabs[0].text == first
    assert tabs[1].text == second
