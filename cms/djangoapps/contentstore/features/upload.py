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


@step(u'I go to the files and uploads page')
def go_to_uploads(step):
    menu_css = 'li.nav-course-courseware'
    uploads_css = '.nav-course-courseware-uploads'
    world.css_find(menu_css).click()
    world.css_find(uploads_css).click()


@step(u'I upload the file "([^"]*)"$')
def upload_file(step, file_name):
    upload_css = '.upload-button'
    world.css_find(upload_css).click()

    file_css = '.file-input'
    upload = world.css_find(file_css)
    #uploading the file itself
    path = os.path.join(TEST_ROOT, 'uploads/', file_name)
    upload._element.send_keys(os.path.abspath(path))

    close_css = '.close-button'
    world.css_find(close_css).click()


@step(u'I see the file "([^"]*)" was uploaded$')
def check_upload(step, file_name):
    index = get_index(file_name)
    assert index != -1


@step(u'The url for the file "([^"]*)" is valid$')
def check_url(step, file_name):
    r = get_file(file_name)
    assert r.status_code == 200


@step(u'I see only one "([^"]*)"$')
def no_duplicate(step, file_name):
    names_css = '.name-col > a.filename'
    all_names = world.css_find(names_css)
    only_one = False
    for i in range(len(all_names)):
        if file_name == all_names[i].html:
            only_one = not only_one
    assert only_one


@step(u'I can download the correct "([^"]*)" file$')
def check_download(step, file_name):
    path = os.path.join(TEST_ROOT, 'uploads/', file_name)
    with open(os.path.abspath(path), 'r') as cur_file:
        cur_text = cur_file.read()
        r = get_file(file_name)
        downloaded_text = r.text
        assert cur_text == downloaded_text


@step(u'I modify "([^"]*)"$')
def modify_upload(step, file_name):
    new_text = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(10))
    path = os.path.join(TEST_ROOT, 'uploads/', file_name)
    with open(os.path.abspath(path), 'w') as cur_file:
        cur_file.write(new_text)


def get_index(file_name):
    names_css = '.name-col > a.filename'
    all_names = world.css_find(names_css)
    for i in range(len(all_names)):
        if file_name == all_names[i].html:
            return i
    return -1


def get_file(file_name):
    index = get_index(file_name)
    assert index != -1

    url_css = 'input.embeddable-xml-input'
    url = world.css_find(url_css)[index].value
    return requests.get(HTTP_PREFIX + url)
