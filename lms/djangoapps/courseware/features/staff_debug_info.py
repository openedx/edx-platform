"""
Steps for staff_debug_info.feature lettuce tests
"""

from django.contrib.auth.models import User
from lettuce import world, step
from common import create_course, course_id
from courseware.courses import get_course_by_id
from instructor.access import allow_access


@step(u'i am staff member for the course "([^"]*)"$')
def i_am_staff_member_for_the_course(step, course_number):
    # Create the course
    create_course(step, course_number)
    course = get_course_by_id(course_id(course_number))

    # Create the user
    world.create_user('robot', 'test')
    user = User.objects.get(username='robot')

    # Add user as a course staff.
    allow_access(course, user, "staff")

    world.log_in(username='robot', password='test')


@step(u'I can view staff debug info')
def view_staff_debug_info(step):
    css_selector = "a.instructor-info-action"
    world.css_click(css_selector)
    world.wait_for_visible("section.staff-modal")


@step(u'I can reset student attempts')
def view_staff_debug_info(step):
    css_selector = "a.staff-debug-reset"
    world.css_click(css_selector)
    world.wait_for_ajax_complete()


@step(u'I cannot see delete student state link')
def view_staff_debug_info(step):
    css_selector = "a.staff-debug-sdelete"
    world.is_css_not_present(css_selector)


@step(u'I cannot see rescore student submission link')
def view_staff_debug_info(step):
    css_selector = "a.staff-debug-rescore"
    world.is_css_not_present(css_selector)
