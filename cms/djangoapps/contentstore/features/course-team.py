#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from nose.tools import assert_in  # pylint: disable=E0611


@step(u'(I am viewing|s?he views) the course team settings$')
def view_grading_settings(_step, whom):
    world.click_course_settings()
    link_css = 'li.nav-course-settings-team a'
    world.css_click(link_css)


@step(u'I add "([^"]*)" to the course team$')
def add_other_user(_step, name):
    new_user_css = 'a.create-user-button'
    world.css_click(new_user_css)

    # Wait for the css animation to apply the is-shown class
    shown_css = 'div.wrapper-create-user.is-shown'
    world.wait_for_present(shown_css)

    email_css = 'input#user-email-input'
    world.css_fill(email_css, name + '@edx.org')
    if world.is_firefox():
        world.trigger_event(email_css)
    confirm_css = 'form.create-user button.action-primary'
    world.css_click(confirm_css)


@step(u'I delete "([^"]*)" from the course team$')
def delete_other_user(_step, name):
    to_delete_css = '.user-item .item-actions a.remove-user[data-id="{email}"]'.format(
        email="{0}{1}".format(name, '@edx.org'))
    world.css_click(to_delete_css)
    world.confirm_studio_prompt()


@step(u's?he deletes me from the course team$')
def other_delete_self(_step):
    to_delete_css = '.user-item .item-actions a.remove-user[data-id="{email}"]'.format(
        email="robot+studio@edx.org")
    world.css_click(to_delete_css)
    world.confirm_studio_prompt()


@step(u'I make "([^"]*)" a course team admin$')
def make_course_team_admin(_step, name):
    admin_btn_css = '.user-item[data-email="{name}@edx.org"] .user-actions .add-admin-role'.format(
        name=name)
    world.css_click(admin_btn_css)


@step(u'I remove admin rights from ("([^"]*)"|myself)$')
def remove_course_team_admin(_step, outer_capture, name):
    if outer_capture == "myself":
        email = world.scenario_dict["USER"].email
    else:
        email = name + '@edx.org'
    admin_btn_css = '.user-item[data-email="{email}"] .user-actions .remove-admin-role'.format(
        email=email)
    world.css_click(admin_btn_css)


@step(u'I( do not)? see the course on my page$')
@step(u's?he does( not)? see the course on (his|her) page$')
def see_course(_step, do_not_see, gender='self'):
    class_css = 'h3.course-title'
    if do_not_see:
        assert world.is_css_not_present(class_css)
    else:
        all_courses = world.css_find(class_css)
        all_names = [item.html for item in all_courses]
        assert_in(world.scenario_dict['COURSE'].display_name, all_names)


@step(u'"([^"]*)" should( not)? be marked as an admin$')
def marked_as_admin(_step, name, not_marked_admin):
    flag_css = '.user-item[data-email="{name}@edx.org"] .flag-role.flag-role-admin'.format(
        name=name)
    if not_marked_admin:
        assert world.is_css_not_present(flag_css)
    else:
        assert world.is_css_present(flag_css)


@step(u'I should( not)? be marked as an admin$')
def self_marked_as_admin(_step, not_marked_admin):
    return marked_as_admin(_step, "robot+studio", not_marked_admin)


@step(u'I can(not)? delete users$')
@step(u's?he can(not)? delete users$')
def can_delete_users(_step, can_not_delete):
    to_delete_css = 'a.remove-user'
    if can_not_delete:
        assert world.is_css_not_present(to_delete_css)
    else:
        assert world.is_css_present(to_delete_css)


@step(u'I can(not)? add users$')
@step(u's?he can(not)? add users$')
def can_add_users(_step, can_not_add):
    add_css = 'a.create-user-button'
    if can_not_add:
        assert world.is_css_not_present(add_css)
    else:
        assert world.is_css_present(add_css)


@step(u'I can(not)? make ("([^"]*)"|myself) a course team admin$')
@step(u's?he can(not)? make ("([^"]*)"|me) a course team admin$')
def can_make_course_admin(_step, can_not_make_admin, outer_capture, name):
    if outer_capture == "myself":
        email = world.scenario_dict["USER"].email
    else:
        email = name + '@edx.org'
    add_button_css = '.user-item[data-email="{email}"] .add-admin-role'.format(email=email)
    if can_not_make_admin:
        assert world.is_css_not_present(add_button_css)
    else:
        assert world.is_css_present(add_button_css)
