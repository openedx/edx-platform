# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

from lettuce import world, step
from django.conf import settings
from common import upload_file
from nose.tools import assert_equal

TEST_ROOT = settings.COMMON_TEST_DATA_ROOT


@step(u'I go to the textbooks page')
def go_to_uploads(_step):
    world.wait_for_js_to_load()
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
def upload_textbook(_step, file_name):
    upload_file(file_name, sub_path="uploads/")


@step(u'I click (on )?the New Textbook button')
def click_new_textbook(_step, on):
    button_css = ".nav-actions .new-button"
    button = world.css_find(button_css)
    button.click()


@step(u'I name my textbook "([^"]*)"')
def name_textbook(_step, name):
    input_css = ".textbook input[name=textbook-name]"
    world.css_fill(input_css, name)
    if world.is_firefox():
        world.trigger_event(input_css)


@step(u'I name the (first|second|third) chapter "([^"]*)"')
def name_chapter(_step, ordinal, name):
    index = ["first", "second", "third"].index(ordinal)
    input_css = ".textbook .chapter{i} input.chapter-name".format(i=index + 1)
    world.css_fill(input_css, name)
    if world.is_firefox():
        world.trigger_event(input_css)


@step(u'I type in "([^"]*)" for the (first|second|third) chapter asset')
def asset_chapter(_step, name, ordinal):
    index = ["first", "second", "third"].index(ordinal)
    input_css = ".textbook .chapter{i} input.chapter-asset-path".format(i=index + 1)
    world.css_fill(input_css, name)
    if world.is_firefox():
        world.trigger_event(input_css)


@step(u'I click the Upload Asset link for the (first|second|third) chapter')
def click_upload_asset(_step, ordinal):
    index = ["first", "second", "third"].index(ordinal)
    button_css = ".textbook .chapter{i} .action-upload".format(i=index + 1)
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
    title = world.css_text(".textbook h3.textbook-title", index=0)
    chapter = world.css_text(".textbook .wrap-textbook p", index=0)
    assert_equal(title, textbook_name)
    assert_equal(chapter, chapter_name)


@step(u'I should see a textbook named "([^"]*)" with (\d+) chapters')
def check_textbook_chapters(_step, textbook_name, num_chapters_str):
    num_chapters = int(num_chapters_str)
    title = world.css_text(".textbook .view-textbook h3.textbook-title", index=0)
    toggle_text = world.css_text(".textbook .view-textbook .chapter-toggle", index=0)
    assert_equal(title, textbook_name)
    assert_equal(
        toggle_text,
        "{num} PDF Chapters".format(num=num_chapters),
        "Expected {num} chapters, found {real}".format(num=num_chapters, real=toggle_text)
    )


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
