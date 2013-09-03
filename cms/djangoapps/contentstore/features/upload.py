#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from django.conf import settings
import requests
import string
import random
import os

TEST_ROOT = settings.COMMON_TEST_DATA_ROOT


@step(u'I go to the files and uploads page')
def go_to_uploads(_step):
    menu_css = 'li.nav-course-courseware'
    uploads_css = 'li.nav-course-courseware-uploads a'
    world.css_click(menu_css)
    world.css_click(uploads_css)


@step(u'I upload the file "([^"]*)"$')
def upload_file(_step, file_name):
    upload_css = 'a.upload-button'
    world.css_click(upload_css)
    #uploading the file itself
    path = os.path.join(TEST_ROOT, 'uploads/', file_name)
    world.browser.execute_script("$('input.file-input').css('display', 'block')")
    world.browser.attach_file('file', os.path.abspath(path))
    close_css = 'a.close-button'
    world.css_click(close_css)


@step(u'I should( not)? see the file "([^"]*)" was uploaded$')
def check_upload(_step, do_not_see_file, file_name):
    index = get_index(file_name)
    if do_not_see_file:
        assert index == -1
    else:
        assert index != -1


@step(u'The url for the file "([^"]*)" is valid$')
def check_url(_step, file_name):
    r = get_file(file_name)
    assert r.status_code == 200


@step(u'I delete the file "([^"]*)"$')
def delete_file(_step, file_name):
    index = get_index(file_name)
    assert index != -1
    delete_css = "a.remove-asset-button"
    world.css_click(delete_css, index=index)

    prompt_confirm_css = 'li.nav-item > a.action-primary'
    world.css_click(prompt_confirm_css, success_condition=lambda: not world.css_visible(prompt_confirm_css))


@step(u'I should see only one "([^"]*)"$')
def no_duplicate(_step, file_name):
    names_css = 'td.name-col > a.filename'
    all_names = world.css_find(names_css)
    only_one = False
    for i in range(len(all_names)):
        if file_name == world.css_html(names_css, index=i):
            only_one = not only_one
    assert only_one


@step(u'I can download the correct "([^"]*)" file$')
def check_download(_step, file_name):
    path = os.path.join(TEST_ROOT, 'uploads/', file_name)
    with open(os.path.abspath(path), 'r') as cur_file:
        cur_text = cur_file.read()
        r = get_file(file_name)
        downloaded_text = r.text
        assert cur_text == downloaded_text
    #resetting the file back to its original state
    with open(os.path.abspath(path), 'w') as cur_file:
        cur_file.write("This is an arbitrary file for testing uploads")


@step(u'I modify "([^"]*)"$')
def modify_upload(_step, file_name):
    new_text = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(10))
    path = os.path.join(TEST_ROOT, 'uploads/', file_name)
    with open(os.path.abspath(path), 'w') as cur_file:
        cur_file.write(new_text)


@step('I see a confirmation that the file was deleted')
def i_see_a_delete_confirmation(_step):
    alert_css = '#notification-confirmation'
    assert world.is_css_present(alert_css)


def get_index(file_name):
    names_css = 'td.name-col > a.filename'
    all_names = world.css_find(names_css)
    for i in range(len(all_names)):
        if file_name == world.css_html(names_css, index=i):
            return i
    return -1


def get_file(file_name):
    index = get_index(file_name)
    assert index != -1
    url_css = 'a.filename'

    def get_url():
        return world.css_find(url_css)[index]._element.get_attribute('href')
    url = world.retry_on_exception(get_url)
    return requests.get(url)
