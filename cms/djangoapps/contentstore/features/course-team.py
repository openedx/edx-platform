#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from common import create_studio_user, COURSE_NAME

PASS = 'test'
EXTENSION = '@edx.org'


@step(u'I am viewing the course team settings')
def view_grading_settings(step):
    world.click_course_settings()
    link_css = 'li.nav-course-settings-team a'
    world.css_click(link_css)


@step(u'The user "([^"]*)" exists$')
def create_other_user(step, name):
    create_studio_user(uname=name, password=PASS, email=(name + EXTENSION))


@step(u'I add "([^"]*)" to the course team')
def add_other_user(step, name):
    new_user_css = '.new-user-button'
    world.css_find(new_user_css).click()

    email_css = '.email-input'
    f = world.css_find(email_css)
    f._element.send_keys(name, EXTENSION)

    confirm_css = '#add_user'
    world.css_find(confirm_css).click()


@step(u'I delete "([^"]*)" from the course team')
def delete_other_user(step, name):
    to_delete_css = '.remove-user[data-id="%s%s"]' % (name, EXTENSION,)
    world.css_find(to_delete_css).click()


@step(u'"([^"]*)" logs in$')
def other_user_login(step, name):
    world.browser.cookies.delete()
    world.visit('/')

    signin_css = 'a.action-signin'
    world.is_css_present(signin_css)
    world.css_click(signin_css)

    login_form = world.browser.find_by_css('form#login_form')
    login_form.find_by_name('email').fill(name + EXTENSION)
    login_form.find_by_name('password').fill(PASS)
    login_form.find_by_name('submit').click()


@step(u'He does( not)? see the course on his page')
def see_course(step, doesnt):
    class_css = '.class-name'
    all_courses = world.css_find(class_css)
    all_names = [item.html for item in all_courses]
    if doesnt:
        assert not COURSE_NAME in all_names
    else:
        assert COURSE_NAME in all_names


@step(u'He cannot delete users')
def cannot_delete(step):
    to_delete_css = '.remove-user'
    assert world.is_css_not_present(to_delete_css)


@step(u'He cannot add users')
def cannot_add(step):
    add_css = '.new-user'
    assert world.is_css_not_present(add_css)
