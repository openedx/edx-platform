#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
import os


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
    upload._element.send_keys(os.path.dirname(__file__) + '/' + file_name)

    close_css = '.close-button'
    world.css_find(close_css).click()


@step(u'I see the file "([^"]*)" was uploaded')
def check_upload(step, file_name):
    index = get_index(file_name)
    assert index != -1


@step(u'I see only one "([^"]*)"$')
def no_duplicate(step, file_name):
    names_css = '.name-col > a.filename'
    all_names = world.css_find(names_css)
    only_one = False
    for i in range(len(all_names)):
        if file_name == all_names[i].html:
            only_one = not only_one
    assert only_one


def get_index(file_name):
    names_css = '.name-col > a.filename'
    all_names = world.css_find(names_css)
    for i in range(len(all_names)):
        if file_name == all_names[i].html:
            return i
    return -1
