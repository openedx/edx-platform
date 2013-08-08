#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from selenium.webdriver.common.keys import Keys
from common import type_in_codemirror


@step(u'I go to the course updates page')
def go_to_updates(_step):
    menu_css = 'li.nav-course-courseware'
    updates_css = 'li.nav-course-courseware-updates a'
    world.css_click(menu_css)
    world.css_click(updates_css)


@step(u'I add a new update with the text "([^"]*)"$')
def add_update(_step, text):
    update_css = 'a.new-update-button'
    world.css_click(update_css)
    change_text(text)


@step(u'I should( not)? see the update "([^"]*)"$')
def check_update(_step, doesnt_see_update, text):
    update_css = 'div.update-contents'
    update = world.css_find(update_css, wait_time=1)
    if doesnt_see_update:
        assert len(update) == 0 or not text in update.html
    else:
        assert text in update.html


@step(u'I modify the text to "([^"]*)"$')
def modify_update(_step, text):
    button_css = 'div.post-preview a.edit-button'
    world.css_click(button_css)
    change_text(text)


@step(u'I delete the update$')
def click_button(_step):
    button_css = 'div.post-preview a.delete-button'
    world.css_click(button_css)


@step(u'I edit the date to "([^"]*)"$')
def change_date(_step, new_date):
    button_css = 'div.post-preview a.edit-button'
    world.css_click(button_css)
    date_css = 'input.date'
    date = world.css_find(date_css)
    for i in range(len(date.value)):
        date._element.send_keys(Keys.END, Keys.BACK_SPACE)
    date._element.send_keys(new_date)
    save_css = 'a.save-button'
    world.css_click(save_css)


@step(u'I should see the date "([^"]*)"$')
def check_date(_step, date):
    date_css = 'span.date-display'
    assert date == world.css_html(date_css)


@step(u'I modify the handout to "([^"]*)"$')
def edit_handouts(_step, text):
    edit_css = 'div.course-handouts > a.edit-button'
    world.css_click(edit_css)
    change_text(text)


@step(u'I see the handout "([^"]*)"$')
def check_handout(_step, handout):
    handout_css = 'div.handouts-content'
    assert handout in world.css_html(handout_css)


def change_text(text):
    type_in_codemirror(0, text)
    save_css = 'a.save-button'
    world.css_click(save_css)
