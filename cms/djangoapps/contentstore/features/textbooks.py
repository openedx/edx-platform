#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from django.conf import settings
import requests
import string
import random
import os

TEST_ROOT = settings.COMMON_TEST_DATA_ROOT
HTTP_PREFIX = "http://localhost:8001"


@step(u'I go to the textbooks page')
def go_to_uploads(_step):
    world.click_course_content()
    menu_css = 'li.nav-course-courseware-textbooks'
    world.css_find(menu_css).click()

@step(u'I should see a message telling me to create a new textbook')
def assert_create_new_textbook_msg(_step):
    css = ".wrapper-content .no-textbook-content"
    assert world.is_css_present(css)
    no_tb = world.css_find(css)
    assert "You haven't added any textbooks" in no_tb.text

@step(u'I upload the textbook "([^"]*)"$')
def upload_file(_step, file_name):
    file_css = '.upload-dialog input[type=file]'
    upload = world.css_find(file_css)
    # uploading the file itself
    path = os.path.join(TEST_ROOT, 'uploads', file_name)
    upload._element.send_keys(os.path.abspath(path))
    button_css = ".upload-dialog .action-upload"
    world.css_click(button_css)

@step(u'I click (on )?the New Textbook button')
def click_new_textbook(_step, on):
    button_css = ".nav-actions .new-button"
    button = world.css_find(button_css)
    button.click()

@step(u'I name my textbook "([^"]*)"')
def name_textbook(_step, name):
    input_css = ".textbook input[name=textbook-name]"
    world.css_fill(input_css, name)

@step(u'I name the first chapter "([^"]*)"')
def name_chapter(_step, name):
    input_css = ".textbook input.chapter-name"
    world.css_fill(input_css, name)

@step(u'I click the Upload Asset link for the first chapter')
def click_upload_asset(_step):
    button_css = ".chapter .action-upload"
    world.css_click(button_css)

@step(u'I save the textbook')
def save_textbook(_step):
    submit_css = "form.edit-textbook button[type=submit]"
    world.css_click(submit_css)

@step(u'I should see a textbook named "([^"]*)" with a chapter path containing "([^"]*)"')
def check_textbook(step, textbook_name, chapter_name):
    title = world.css_find(".textbook h3.textbook-title")
    chapter = world.css_find(".textbook .wrap-textbook p")
    assert title.text == textbook_name, "{} != {}".format(title.text, textbook_name)
    assert chapter.text == chapter_name, "{} != {}".format(chapter.text, chapter_name)

