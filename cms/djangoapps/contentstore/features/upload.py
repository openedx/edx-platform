#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from django.conf import settings
import requests
import string
import random
import os
from nose.tools import assert_equal, assert_not_equal # pylint: disable=E0611


TEST_ROOT = settings.COMMON_TEST_DATA_ROOT
ASSET_NAMES_CSS = 'td.name-col > span.title > a.filename'


@step(u'I go to the files and uploads page$')
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


@step(u'I upload the files (".*")$')
def upload_files(_step, files_string):
    # Turn files_string to a list of file names
    files = files_string.split(",")
    files = map(lambda x: string.strip(x, ' "\''), files)

    upload_css = 'a.upload-button'
    world.css_click(upload_css)
    #uploading the files
    for f in files:
        path = os.path.join(TEST_ROOT, 'uploads/', f)
        world.browser.execute_script("$('input.file-input').css('display', 'block')")
        world.browser.attach_file('file', os.path.abspath(path))
    close_css = 'a.close-button'
    world.css_click(close_css)


@step(u'I should not see the file "([^"]*)" was uploaded$')
def check_not_there(_step, file_name):
    # Either there are no files, or there are files but
    # not the one I expect not to exist.

    # Since our only test for deletion right now deletes
    # the only file that was uploaded, our success criteria
    # will be that there are no files.
    # In the future we can refactor if necessary.
    assert(world.is_css_not_present(ASSET_NAMES_CSS))


@step(u'I should see the file "([^"]*)" was uploaded$')
def check_upload(_step, file_name):
    index = get_index(file_name)
    assert_not_equal(index, -1)


@step(u'The url for the file "([^"]*)" is valid$')
def check_url(_step, file_name):
    r = get_file(file_name)
    assert_equal(r.status_code , 200)


@step(u'I delete the file "([^"]*)"$')
def delete_file(_step, file_name):
    index = get_index(file_name)
    assert index != -1
    delete_css = "a.remove-asset-button"
    world.css_click(delete_css, index=index)

    prompt_confirm_css = 'li.nav-item > a.action-primary'
    world.css_click(prompt_confirm_css)


@step(u'I should see only one "([^"]*)"$')
def no_duplicate(_step, file_name):
    all_names = world.css_find(ASSET_NAMES_CSS)
    only_one = False
    for i in range(len(all_names)):
        if file_name == world.css_html(ASSET_NAMES_CSS, index=i):
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
    _write_test_file(file_name, "This is an arbitrary file for testing uploads")


def _write_test_file(file_name, text):
    path = os.path.join(TEST_ROOT, 'uploads/', file_name)
    #resetting the file back to its original state
    with open(os.path.abspath(path), 'w') as cur_file:
        cur_file.write(text)


@step(u'I modify "([^"]*)"$')
def modify_upload(_step, file_name):
    new_text = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(10))
    _write_test_file(file_name, new_text)


@step(u'I (lock|unlock) "([^"]*)"$')
def lock_unlock_file(_step, _lock_state, file_name):
    index = get_index(file_name)
    assert index != -1
    lock_css = "a.lock-asset-button"
    world.css_click(lock_css, index=index)


@step(u'Then "([^"]*)" is (locked|unlocked)$')
def verify_lock_unlock_file(_step, file_name, lock_state):
    index = get_index(file_name)
    assert index != -1
    lock_css = "a.lock-asset-button"
    text = world.css_text(lock_css, index=index)
    if lock_state == "locked":
        assert_equal("Unlock this asset", text)
    else:
        assert_equal("Lock this asset", text)


@step(u'I have opened a course with a (locked|unlocked) asset "([^"]*)"$')
def open_course_with_locked(step, lock_state, file_name):
    step.given('I have opened a new course in studio')
    step.given('I go to the files and uploads page')
    _write_test_file(file_name, "test file")
    step.given('I upload the file "' + file_name + '"')
    if lock_state == "locked":
        step.given('I lock "' + file_name + '"')
        step.given('I reload the page')


@step(u'Then the asset "([^"]*)" is (viewable|protected)$')
def view_asset(_step, file_name, status):
    url = '/c4x/MITx/999/asset/' + file_name
    if status == 'viewable':
        world.visit(url)
        _verify_body_text()
    else:
        error_thrown = False
        try:
            world.visit(url)
        except Exception as e:
            assert e.status_code == 403
            error_thrown = True
        assert error_thrown


@step(u'Then the asset "([^"]*)" can be clicked from the asset index$')
def click_asset_from_index(step, file_name):
    # This is not ideal, but I'm having trouble with the middleware not having
    # the same user in the request when I hit the URL directly.
    course_link_css = 'a.course-link'
    world.css_click(course_link_css)
    step.given("I go to the files and uploads page")
    index = get_index(file_name)
    assert index != -1
    world.css_click('a.filename', index=index)
    _verify_body_text()


def _verify_body_text():
    def verify_text(driver):
        return world.css_text('body') == 'test file'

    world.wait_for(verify_text)


@step('I see a confirmation that the file was deleted$')
def i_see_a_delete_confirmation(_step):
    alert_css = '#notification-confirmation'
    assert world.is_css_present(alert_css)


def get_index(file_name):
    all_names = world.css_find(ASSET_NAMES_CSS)
    for i in range(len(all_names)):
        if file_name == world.css_html(ASSET_NAMES_CSS, index=i):
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
