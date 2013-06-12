#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from selenium.webdriver.common.keys import Keys


@step(u'I go to the course updates page')
def go_to_uploads(step):
    menu_css = 'li.nav-course-courseware'
    uploads_css = '.nav-course-courseware-updates'
    world.css_click(menu_css)
    world.css_click(uploads_css)


@step(u'I add a new update with the text "([^"]*)"$')
def add_update(step, text):
    update_css = '.new-update-button'
    world.css_click(update_css)
    change_text(text)


@step(u'I should( not)? see the update "([^"]*)"$')
def check_update(step, doesnt_see_update, text):
    update_css = '.update-contents'
    update = world.css_find(update_css)
    if doesnt_see_update:
        assert len(update) == 0 or not text in update.html
    else:
        assert text in update.html


@step(u'I modify the text to "([^"]*)"$')
def modify_update(step, text):
    button_css = '.post-preview .edit-button'
    world.css_click(button_css)
    change_text(text)


@step(u'I delete the update$')
def click_button(step):
    button_css = '.post-preview .delete-button'
    world.css_click(button_css)


@step(u'I edit the date to "([^"]*)"$')
def change_date(step, new_date):
    button_css = '.post-preview .edit-button'
    world.css_click(button_css)
    date_css = 'input.date'
    date = world.css_find(date_css)
    for i in range(len(date.value)):
        date._element.send_keys(Keys.END, Keys.BACK_SPACE)
    date._element.send_keys(new_date)
    save_css = '.save-button'
    world.css_click(save_css)


@step(u'I should see the date "([^"]*)"$')
def check_date(step, date):
    date_css = '.date-display'
    date_html = world.css_find(date_css)
    assert date == date_html.html


@step(u'I modify the handout to "([^"]*)"$')
def edit_handouts(step, text):
    edit_css = '.course-handouts > .edit-button'
    world.css_click(edit_css)
    change_text(text)


@step(u'I see the handout "([^"]*)"$')
def check_handout(step, handout):
    handout_css = '.handouts-content'
    handouts = world.css_find(handout_css)
    assert handout in handouts.html


def change_text(text):
    text_css = 'div.CodeMirror > div > textarea'
    prev_css = 'div.CodeMirror-lines > div > div:last-child > pre'
    all_lines = world.css_find(prev_css)
    all_text = ''
    for i in range(len(all_lines)):
        all_text = all_lines[i].html
    text_area = world.css_find(text_css)
    for i in range(len(all_text)):
        text_area._element.send_keys(Keys.END, Keys.BACK_SPACE)
    text_area._element.send_keys(text)
    save_css = '.save-button'
    world.css_click(save_css)
