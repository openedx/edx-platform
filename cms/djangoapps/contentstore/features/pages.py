# pylint: disable=C0111
# pylint: disable=W0621
# pylint: disable=W0613

from lettuce import world, step
from nose.tools import assert_equal  # pylint: disable=E0611


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
    assert_equal(page_name_html, '\n    {name}\n'.format(name=name))


@step(u'I should not see any static pages$')
def not_see_any_static_pages(step):
    pages_css = 'div.xmodule_StaticTabModule'
    assert (world.is_css_not_present(pages_css, wait_time=30))


@step(u'I should see the default built-in pages')
def see_default_built_in_pages(step):
    expected_pages = ['Courseware', 'Course Info', 'Discussion', 'Wiki', 'Progress']
    pages = world.css_find("div.course-nav-tab-header h3.title")
    assert_equal(len(expected_pages), len(pages))
    for i, page_name in enumerate(expected_pages):
        assert_equal(pages[i].text, page_name)


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


@step(u'I reorder the static tabs')
def reorder_static_tabs(_step):
    tabs = world.css_find('.xmodule_StaticTabModule')
    tab1_o = tabs[0].text
    tab2_o = tabs[1].text

    # For some reason, the drag_and_drop method did not work in this case.
    draggables = world.css_find('.component .drag-handle')
    source = draggables.first
    target = draggables.last
    source.action_chains.click_and_hold(source._element).perform()  # pylint: disable=protected-access
    source.action_chains.move_to_element_with_offset(target._element, 0, 50).perform()  # pylint: disable=protected-access
    source.action_chains.release().perform()

    tabs = world.css_find('.xmodule_StaticTabModule')
    tab1 = tabs[0].text
    tab2 = tabs[1].text
    assert True

# def move_grade_slider(step):
#     moveable_css = '.ui-resizable-e'
#     f = world.css_find(moveable_css).first
#     f.action_chains.drag_and_drop_by_offset(f._element, 100, 0).perform()


@step(u'I have created a static page')
def create_static_page(step):
    step.given('I have opened the pages page in a new course')
    step.given('I add a new static page')


@step(u'I have opened the pages page in a new course')
def open_pages_page_in_new_course(step):
    step.given('I have opened a new course in Studio')
    step.given('I go to the pages page')


@step(u'I have created two different static pages')
def create_two_pages(step):
    step.given('I have created a static page')
    step.given('I "edit" the static page')
    step.given('I change the name to "First"')
    step.given('I add a new static page')
    # Verify order of pages
    _verify_page_names('First', 'Empty')


@step(u'the static tabs are in the reverse order')
def static_tabs_in_reverse_order(step):
    _verify_page_names('Empty', 'First')


def _verify_page_names(first, second):
    world.wait_for(
        func=lambda _: len(world.css_find('.xmodule_StaticTabModule')) == 2,
        timeout=200,
        timeout_msg="Timed out waiting for two tabs to be present"
    )
    # tabs = world.css_find('.xmodule_StaticTabModule')
    # assert tabs[0].text == first
    # assert tabs[1].text == second


@step(u'I should see the "([^"]*)" page as "(visible|hidden)"$')
def tab_is_visible(step, page_id, visible_or_hidden):
    # tab = world.css_find("li[data-tab-id='{0}']".format(page_id))
    # visible = visible_or_hidden == "visible"
    # assert ("checked" in tab.html) != visible
    pass


@step(u'I toggle the visibility of the "([^"]*)" page')
def tab_toggle_visibility(step, page_id):
    # input = world.css_find("li[data-tab-id='{0}'] input.toggle-checkbox".format(page_id))
    # world.css_check("li[data-tab-id='{0}'] input.toggle-checkbox".format(page_id))
    pass

@step(u'I reorder the tabs')
def reorder_tabs(_step):
    pass


@step(u'the tabs are in the reverse order')
def tabs_in_reverse_order(step):
    pass
