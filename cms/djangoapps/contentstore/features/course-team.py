#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from common import create_studio_user
from django.contrib.auth.models import Group
from auth.authz import get_course_groupname_for_role, get_user_by_email
from nose.tools import assert_true

PASSWORD = 'test'
EMAIL_EXTENSION = '@edx.org'


@step(u'(I am viewing|s?he views) the course team settings')
def view_grading_settings(_step, whom):
    world.click_course_settings()
    link_css = 'li.nav-course-settings-team a'
    world.css_click(link_css)


@step(u'the user "([^"]*)" exists( as a course (admin|staff member))?$')
def create_other_user(_step, name, has_extra_perms, role_name):
    email = name + EMAIL_EXTENSION
    user = create_studio_user(uname=name, password=PASSWORD, email=email)
    if has_extra_perms:
        location = world.scenario_dict["COURSE"].location
        if role_name == "admin":
            # admins get staff privileges, as well
            roles = ("staff", "instructor")
        else:
            roles = ("staff",)
        for role in roles:
            groupname = get_course_groupname_for_role(location, role)
            group, __ = Group.objects.get_or_create(name=groupname)
            user.groups.add(group)
        user.save()


@step(u'I add "([^"]*)" to the course team')
def add_other_user(_step, name):
    new_user_css = 'a.create-user-button'
    world.css_click(new_user_css)
    world.wait(0.5)

    email_css = 'input#user-email-input'
    world.css_fill(email_css, name + EMAIL_EXTENSION)
    if world.is_firefox():
        world.trigger_event(email_css)
    confirm_css = 'form.create-user button.action-primary'
    world.css_click(confirm_css)


@step(u'I delete "([^"]*)" from the course team')
def delete_other_user(_step, name):
    to_delete_css = '.user-item .item-actions a.remove-user[data-id="{email}"]'.format(
        email="{0}{1}".format(name, EMAIL_EXTENSION))
    world.css_click(to_delete_css)
    # confirm prompt
    # need to wait for the animation to be done, there isn't a good success condition that won't work both on latest chrome and jenkins
    world.wait(.5)
    world.css_click(".wrapper-prompt-warning .action-primary")


@step(u's?he deletes me from the course team')
def other_delete_self(_step):
    to_delete_css = '.user-item .item-actions a.remove-user[data-id="{email}"]'.format(
        email="robot+studio@edx.org")
    world.css_click(to_delete_css)
    # confirm prompt
    world.wait(.5)
    world.css_click(".wrapper-prompt-warning .action-primary")


@step(u'I make "([^"]*)" a course team admin')
def make_course_team_admin(_step, name):
    admin_btn_css = '.user-item[data-email="{email}"] .user-actions .add-admin-role'.format(
        email=name+EMAIL_EXTENSION)
    world.css_click(admin_btn_css)


@step(u'I remove admin rights from ("([^"]*)"|myself)')
def remove_course_team_admin(_step, outer_capture, name):
    if outer_capture == "myself":
        email = world.scenario_dict["USER"].email
    else:
        email = name + EMAIL_EXTENSION
    admin_btn_css = '.user-item[data-email="{email}"] .user-actions .remove-admin-role'.format(
        email=email)
    world.css_click(admin_btn_css)


@step(u'"([^"]*)" logs in$')
def other_user_login(_step, name):
    world.browser.cookies.delete()
    world.visit('/')

    signin_css = 'a.action-signin'
    world.is_css_present(signin_css)
    world.css_click(signin_css)

    def fill_login_form():
        login_form = world.browser.find_by_css('form#login_form')
        login_form.find_by_name('email').fill(name + EMAIL_EXTENSION)
        login_form.find_by_name('password').fill(PASSWORD)
        login_form.find_by_name('submit').click()
    world.retry_on_exception(fill_login_form)
    assert_true(world.is_css_present('.new-course-button'))
    world.scenario_dict['USER'] = get_user_by_email(name + EMAIL_EXTENSION)


@step(u'I( do not)? see the course on my page')
@step(u's?he does( not)? see the course on (his|her) page')
def see_course(_step, inverted, gender='self'):
    class_css = 'h3.course-title'
    all_courses = world.css_find(class_css, wait_time=1)
    all_names = [item.html for item in all_courses]
    if inverted:
        assert not world.scenario_dict['COURSE'].display_name in all_names
    else:
        assert world.scenario_dict['COURSE'].display_name in all_names


@step(u'"([^"]*)" should( not)? be marked as an admin')
def marked_as_admin(_step, name, inverted):
    flag_css = '.user-item[data-email="{email}"] .flag-role.flag-role-admin'.format(
        email=name+EMAIL_EXTENSION)
    if inverted:
        assert world.is_css_not_present(flag_css)
    else:
        assert world.is_css_present(flag_css)


@step(u'I should( not)? be marked as an admin')
def self_marked_as_admin(_step, inverted):
    return marked_as_admin(_step, "robot+studio", inverted)


@step(u'I can(not)? delete users')
@step(u's?he can(not)? delete users')
def can_delete_users(_step, inverted):
    to_delete_css = 'a.remove-user'
    if inverted:
        assert world.is_css_not_present(to_delete_css)
    else:
        assert world.is_css_present(to_delete_css)


@step(u'I can(not)? add users')
@step(u's?he can(not)? add users')
def can_add_users(_step, inverted):
    add_css = 'a.create-user-button'
    if inverted:
        assert world.is_css_not_present(add_css)
    else:
        assert world.is_css_present(add_css)


@step(u'I can(not)? make ("([^"]*)"|myself) a course team admin')
@step(u's?he can(not)? make ("([^"]*)"|me) a course team admin')
def can_make_course_admin(_step, inverted, outer_capture, name):
    if outer_capture == "myself":
        email = world.scenario_dict["USER"].email
    else:
        email = name + EMAIL_EXTENSION
    add_button_css = '.user-item[data-email="{email}"] .add-admin-role'.format(email=email)
    if inverted:
        assert world.is_css_not_present(add_button_css)
    else:
        assert world.is_css_present(add_button_css)
