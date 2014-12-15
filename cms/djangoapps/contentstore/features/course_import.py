# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

import os
from lettuce import world, step
from django.conf import settings


def import_file(filename):
    world.browser.execute_script("$('input.file-input').css('display', 'block')")
    path = os.path.join(settings.COMMON_TEST_DATA_ROOT, "imports", filename)
    world.browser.attach_file('course-data', os.path.abspath(path))
    world.css_click('input.submit-button')
    # Go to course outline
    world.click_course_content()
    outline_css = 'li.nav-course-courseware-outline a'
    world.css_click(outline_css)


@step('I go to the import page$')
def go_to_import(step):
    menu_css = 'li.nav-course-tools'
    import_css = 'li.nav-course-tools-import a'
    world.css_click(menu_css)
    world.css_click(import_css)
