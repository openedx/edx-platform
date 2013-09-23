#pylint: disable=C0111
#pylint: disable=W0621

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
    pages_css = 'section.xmodule_StaticTabModule'
    page_name_html = world.css_html(pages_css)
    assert_equal(page_name_html, '\n    {name}\n'.format(name=name))


@step(u'I should not see any static pages$')
def not_see_any_static_pages(step):
    pages_css = 'section.xmodule_StaticTabModule'
    assert (world.is_css_not_present(pages_css, wait_time=30))


@step(u'I "(edit|delete)" the static page$')
def click_edit_or_delete(step, edit_or_delete):
    button_css = 'div.component-actions a.%s-button' % edit_or_delete
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
