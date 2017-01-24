# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

from __future__ import absolute_import

import time

from lettuce import world, step, before
from lettuce.django import django_url
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore
from xmodule.course_module import CourseDescriptor
from courseware.courses import get_course_by_id
from xmodule import seq_module, vertical_block
from logging import getLogger
logger = getLogger(__name__)


@step('I (.*) capturing of screenshots before and after each step$')
def configure_screenshots_for_all_steps(_step, action):
    """
    A step to be used in *.feature files. Enables/disables
    automatic saving of screenshots before and after each step in a
    scenario.
    """
    action = action.strip()
    if action == 'enable':
        world.auto_capture_screenshots = True
    elif action == 'disable':
        world.auto_capture_screenshots = False
    else:
        raise ValueError('Parameter `action` should be one of "enable" or "disable".')


@world.absorb
def capture_screenshot_before_after(func):
    """
    A decorator that will take a screenshot before and after the applied
    function is run. Use this if you do not want to capture screenshots
    for each step in a scenario, but rather want to debug a single function.
    """
    def inner(*args, **kwargs):
        prefix = round(time.time() * 1000)

        world.capture_screenshot("{}_{}_{}".format(
            prefix, func.func_name, 'before'
        ))
        ret_val = func(*args, **kwargs)
        world.capture_screenshot("{}_{}_{}".format(
            prefix, func.func_name, 'after'
        ))
        return ret_val
    return inner


@step(u'The course "([^"]*)" exists$')
def create_course(_step, course):

    # First clear the modulestore so we don't try to recreate
    # the same course twice
    # This also ensures that the necessary templates are loaded
    world.clear_courses()

    # Create the course
    # We always use the same org and display name,
    # but vary the course identifier (e.g. 600x or 191x)
    world.scenario_dict['COURSE'] = world.CourseFactory.create(
        org='edx',
        number=course,
        display_name='Test Course'
    )

    # Add a chapter to the course to contain problems
    world.scenario_dict['CHAPTER'] = world.ItemFactory.create(
        parent_location=world.scenario_dict['COURSE'].location,
        category='chapter',
        display_name='Test Chapter',
        publish_item=True,  # Not needed for direct-only but I'd rather the test didn't know that
    )

    world.scenario_dict['SECTION'] = world.ItemFactory.create(
        parent_location=world.scenario_dict['CHAPTER'].location,
        category='sequential',
        display_name='Test Section',
        publish_item=True,
    )


@step(u'I am registered for the course "([^"]*)"$')
def i_am_registered_for_the_course(step, course):
    # Create the course
    create_course(step, course)

    # Create the user
    world.create_user('robot', 'test')
    user = User.objects.get(username='robot')

    # If the user is not already enrolled, enroll the user.
    # TODO: change to factory
    CourseEnrollment.enroll(user, course_id(course))

    world.log_in(username='robot', password='test')


@step(u'The course "([^"]*)" has extra tab "([^"]*)"$')
def add_tab_to_course(_step, course, extra_tab_name):
    world.ItemFactory.create(
        parent_location=course_location(course),
        category="static_tab",
        display_name=str(extra_tab_name))


@step(u'I am in a course$')
def go_into_course(step):
    step.given('I am registered for the course "6.002x"')
    step.given('And I am logged in')
    step.given('And I click on View Courseware')


# Do we really use these 3 w/ a different course than is in the scenario_dict? if so, why? If not,
# then get rid of the override arg
def course_id(course_num):
    return world.scenario_dict['COURSE'].id.replace(course=course_num)


def course_location(course_num):
    return world.scenario_dict['COURSE'].location.replace(course=course_num)


def section_location(course_num):
    return world.scenario_dict['SECTION'].location.replace(course=course_num)


def visit_scenario_item(item_key):
    """
    Go to the courseware page containing the item stored in `world.scenario_dict`
    under the key `item_key`
    """

    url = django_url(reverse(
        'jump_to',
        kwargs={
            'course_id': unicode(world.scenario_dict['COURSE'].id),
            'location': unicode(world.scenario_dict[item_key].location),
        }
    ))

    world.browser.visit(url)


def get_courses():
    '''
    Returns dict of lists of courses available, keyed by course.org (ie university).
    Courses are sorted by course.number.
    '''
    courses = [c for c in modulestore().get_courses()
               if isinstance(c, CourseDescriptor)]  # skip error descriptors
    courses = sorted(courses, key=lambda course: course.location.course)
    return courses


def get_courseware_with_tabs(course_id):
    """
    Given a course_id (string), return a courseware array of dictionaries for the
    top three levels of navigation. Same as get_courseware() except include
    the tabs on the right hand main navigation page.

    This hides the appropriate courseware as defined by the hide_from_toc field:
    chapter.hide_from_toc

    Example:

    [{
        'chapter_name': 'Overview',
        'sections': [{
            'clickable_tab_count': 0,
            'section_name': 'Welcome',
            'tab_classes': []
        }, {
            'clickable_tab_count': 1,
            'section_name': 'System Usage Sequence',
            'tab_classes': ['VerticalBlock']
        }, {
            'clickable_tab_count': 0,
            'section_name': 'Lab0: Using the tools',
            'tab_classes': ['HtmlDescriptor', 'HtmlDescriptor', 'CapaDescriptor']
        }, {
            'clickable_tab_count': 0,
            'section_name': 'Circuit Sandbox',
            'tab_classes': []
        }]
    }, {
        'chapter_name': 'Week 1',
        'sections': [{
            'clickable_tab_count': 4,
            'section_name': 'Administrivia and Circuit Elements',
            'tab_classes': ['VerticalBlock', 'VerticalBlock', 'VerticalBlock', 'VerticalBlock']
        }, {
            'clickable_tab_count': 0,
            'section_name': 'Basic Circuit Analysis',
            'tab_classes': ['CapaDescriptor', 'CapaDescriptor', 'CapaDescriptor']
        }, {
            'clickable_tab_count': 0,
            'section_name': 'Resistor Divider',
            'tab_classes': []
        }, {
            'clickable_tab_count': 0,
            'section_name': 'Week 1 Tutorials',
            'tab_classes': []
        }]
    }, {
        'chapter_name': 'Midterm Exam',
        'sections': [{
            'clickable_tab_count': 2,
            'section_name': 'Midterm Exam',
            'tab_classes': ['VerticalBlock', 'VerticalBlock']
        }]
    }]
    """

    course = get_course_by_id(course_id)
    chapters = [chapter for chapter in course.get_children() if not chapter.hide_from_toc]
    courseware = [{
        'chapter_name': c.display_name_with_default_escaped,
        'sections': [{
            'section_name': s.display_name_with_default_escaped,
            'clickable_tab_count': len(s.get_children()) if (type(s) == seq_module.SequenceDescriptor) else 0,
            'tabs': [{
                'children_count': len(t.get_children()) if (type(t) == vertical_block.VerticalBlock) else 0,
                'class': t.__class__.__name__} for t in s.get_children()
            ]
        } for s in c.get_children() if not s.hide_from_toc]
    } for c in chapters]

    return courseware
