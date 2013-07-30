#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from common import create_studio_user, log_into_studio
from django.contrib.auth.models import Group
from auth.authz import get_course_groupname_for_role

PASSWORD = 'test'
EMAIL_EXTENSION = '@edx.org'


@step(u'(I am viewing|s?he views) the course team settings')
def view_grading_settings(_step, whom):
    world.click_course_settings()
    link_css = 'li.nav-course-settings-team a'
    world.css_click(link_css)


@step(u'the user "([^"]*)" exists( as a course admin)?$')
def create_other_user(_step, name, course_admin):
    user = create_studio_user(uname=name, password=PASSWORD, email=(name + EMAIL_EXTENSION))
    if course_admin:
        location = world.scenario_dict["COURSE"].location
        for role in ("staff", "instructor"):
            group, __ = Group.objects.get_or_create(name=get_course_groupname_for_role(location, role))
            user.groups.add(group)
        user.save()


@step(u'I add "([^"]*)" to the course team')
def add_other_user(_step, name):
    new_user_css = 'a.create-user-button'
    world.css_click(new_user_css)
    world.wait(0.5)

    email_css = 'input#user-email-input'
    f = world.css_find(email_css)
    f._element.send_keys(name, EMAIL_EXTENSION)

    confirm_css = 'form.create-user button.action-primary'
    world.css_click(confirm_css)


@step(u'I delete "([^"]*)" from the course team')
def delete_other_user(_step, name):
    to_delete_css = '.user-item .item-actions a.remove-user[data-id="{email}"]'.format(
        email="{0}{1}".format(name, EMAIL_EXTENSION))
    world.css_click(to_delete_css)


@step(u'I make "([^"]*)" a course team admin')
def make_course_team_admin(_step, name):
    admin_btn_css = '.user-item[data-email="{email}"] .user-actions .add-admin-role'.format(
        email=name+EMAIL_EXTENSION)
    world.css_click(admin_btn_css)


@step(u'I remove admin rights from "([^"]*)"')
def remove_course_team_admin(_step, name):
    admin_btn_css = '.user-item[data-email="{email}"] .user-actions .remove-admin-role'.format(
        email=name+EMAIL_EXTENSION)
    world.css_click(admin_btn_css)


@step(u'"([^"]*)" logs in$')
def other_user_login(_step, name):
    log_into_studio(uname=name, password=PASSWORD, email=name + EMAIL_EXTENSION)


@step(u's?he does( not)? see the course on (his|her) page')
def see_course(_step, inverted, gender):
    class_css = 'span.class-name'
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


@step(u's?he can(not)? delete users')
def can_delete_users(_step, inverted):
    to_delete_css = 'a.remove-user'
    if inverted:
        assert world.is_css_not_present(to_delete_css)
    else:
        assert world.is_css_present(to_delete_css)


@step(u's?he can(not)? add users')
def can_add_users(_step, inverted):
    add_css = 'a.create-user-button'
    if inverted:
        assert world.is_css_not_present(add_css)
    else:
        assert world.is_css_present(add_css)
