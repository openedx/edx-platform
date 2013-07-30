#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from django.conf import settings
import os

TEST_ROOT = settings.COMMON_TEST_DATA_ROOT


@step(u'I go to the textbooks page')
def go_to_uploads(_step):
    world.click_course_content()
    menu_css = 'li.nav-course-courseware-textbooks a'
    world.css_click(menu_css)


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


@step(u'I name the (first|second|third) chapter "([^"]*)"')
def name_chapter(_step, ordinal, name):
    index = ["first", "second", "third"].index(ordinal)
    input_css = ".textbook .chapter{i} input.chapter-name".format(i=index+1)
    world.css_fill(input_css, name)


@step(u'I type in "([^"]*)" for the (first|second|third) chapter asset')
def asset_chapter(_step, name, ordinal):
    index = ["first", "second", "third"].index(ordinal)
    input_css = ".textbook .chapter{i} input.chapter-asset-path".format(i=index+1)
    world.css_fill(input_css, name)


@step(u'I click the Upload Asset link for the (first|second|third) chapter')
def click_upload_asset(_step, ordinal):
    index = ["first", "second", "third"].index(ordinal)
    button_css = ".textbook .chapter{i} .action-upload".format(i=index+1)
    world.css_click(button_css)


@step(u'I click Add a Chapter')
def click_add_chapter(_step):
    button_css = ".textbook .action-add-chapter"
    world.css_click(button_css)


@step(u'I save the textbook')
def save_textbook(_step):
    submit_css = "form.edit-textbook button[type=submit]"
    world.css_click(submit_css)


@step(u'I should see a textbook named "([^"]*)" with a chapter path containing "([^"]*)"')
def check_textbook(_step, textbook_name, chapter_name):
    title = world.css_find(".textbook h3.textbook-title")
    chapter = world.css_find(".textbook .wrap-textbook p")
    assert title.text == textbook_name, "{} != {}".format(title.text, textbook_name)
    assert chapter.text == chapter_name, "{} != {}".format(chapter.text, chapter_name)


@step(u'I should see a textbook named "([^"]*)" with (\d+) chapters')
def check_textbook_chapters(_step, textbook_name, num_chapters_str):
    num_chapters = int(num_chapters_str)
    title = world.css_find(".textbook .view-textbook h3.textbook-title")
    toggle = world.css_find(".textbook .view-textbook .chapter-toggle")
    assert title.text == textbook_name, "{} != {}".format(title.text, textbook_name)
    assert toggle.text == "{num} PDF Chapters".format(num=num_chapters), \
        "Expected {num} chapters, found {real}".format(num=num_chapters, real=toggle.text)


@step(u'I click the textbook chapters')
def click_chapters(_step):
    world.css_click(".textbook a.chapter-toggle")


@step(u'the (first|second|third) chapter should be named "([^"]*)"')
def check_chapter_name(_step, ordinal, name):
    index = ["first", "second", "third"].index(ordinal)
    chapter = world.css_find(".textbook .view-textbook ol.chapters li")[index]
    element = chapter.find_by_css(".chapter-name")
    assert element.text == name, "Expected chapter named {expected}, found chapter named {actual}".format(
        expected=name, actual=element.text)


@step(u'the (first|second|third) chapter should have an asset called "([^"]*)"')
def check_chapter_asset(_step, ordinal, name):
    index = ["first", "second", "third"].index(ordinal)
    chapter = world.css_find(".textbook .view-textbook ol.chapters li")[index]
    element = chapter.find_by_css(".chapter-asset-path")
    assert element.text == name, "Expected chapter with asset {expected}, found chapter with asset {actual}".format(
        expected=name, actual=element.text)
