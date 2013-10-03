#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from lettuce.django import django_url
from django.conf import settings
import requests
import string
import random
import os
from django.contrib.auth.models import User
from student.models import CourseEnrollment
from splinter.request_handler.status_code import HttpResponseError
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

    _write_test_file(file_name, "test file")

    # uploading the file itself
    path = os.path.join(TEST_ROOT, 'uploads/', file_name)
    world.browser.execute_script("$('input.file-input').css('display', 'block')")
    world.browser.attach_file('file', os.path.abspath(path))
    close_css = 'a.close-button'
    world.css_click(close_css)


@step(u'I upload the files "([^"]*)"$')
def upload_files(_step, files_string):
    # files_string should be comma separated with no spaces.
    files = files_string.split(",")
    upload_css = 'a.upload-button'
    world.css_click(upload_css)

    # uploading the files
    for filename in files:
        _write_test_file(filename, "test file")
        path = os.path.join(TEST_ROOT, 'uploads/', filename)
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
    # resetting the file back to its original state
    _write_test_file(file_name, "This is an arbitrary file for testing uploads")


def _write_test_file(file_name, text):
    path = os.path.join(TEST_ROOT, 'uploads/', file_name)
    # resetting the file back to its original state
    with open(os.path.abspath(path), 'w') as cur_file:
        cur_file.write(text)


@step(u'I modify "([^"]*)"$')
def modify_upload(_step, file_name):
    new_text = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(10))
    _write_test_file(file_name, new_text)


@step(u'I upload an asset$')
def upload_an_asset(step):
    step.given('I upload the file "asset.html"')


@step(u'I (lock|unlock) the asset$')
def lock_unlock_file(_step, _lock_state):
    index = get_index('asset.html')
    assert index != -1, 'Expected to find an asset but could not.'

    # Warning: this is a misnomer, it really only toggles the
    # lock state. TODO: fix it.
    lock_css = "input.lock-checkbox"
    world.css_find(lock_css)[index].click()


@step(u'the user "([^"]*)" is enrolled in the course$')
def user_foo_is_enrolled_in_the_course(step, name):
    world.create_user(name, 'test')
    user = User.objects.get(username=name)

    course_id = world.scenario_dict['COURSE'].location.course_id
    CourseEnrollment.enroll(user, course_id)


@step(u'Then the asset is (locked|unlocked)$')
def verify_lock_unlock_file(_step, lock_state):
    index = get_index('asset.html')
    assert index != -1, 'Expected to find an asset but could not.'
    lock_css = "input.lock-checkbox"
    checked = world.css_find(lock_css)[index]._element.get_attribute('checked')
    assert_equal(lock_state == "locked", bool(checked))


@step(u'I am at the files and upload page of a Studio course')
def at_upload_page(step):
    step.given('I have opened a new course in studio')
    step.given('I go to the files and uploads page')


@step(u'I have created a course with a (locked|unlocked) asset$')
def open_course_with_locked(step, lock_state):
    step.given('I am at the files and upload page of a Studio course')
    step.given('I upload the file "asset.html"')

    if lock_state == "locked":
        step.given('I lock the asset')
        step.given('I reload the page')


@step(u'Then the asset is (viewable|protected)$')
def view_asset(_step, status):
    url = django_url('/c4x/MITx/999/asset/asset.html')
    if status == 'viewable':
        expected_text = 'test file'
    else:
        expected_text = 'Unauthorized'

    # Note that world.visit would trigger a 403 error instead of displaying "Unauthorized"
    # Instead, we can drop back into the selenium driver get command.
    world.browser.driver.get(url)
    assert_equal(world.css_text('body'),expected_text)


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
