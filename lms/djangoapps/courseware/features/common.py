# pylint: disable=C0111
# pylint: disable=W0621

from __future__ import absolute_import

from lettuce import world, step
from nose.tools import assert_equals, assert_in
from lettuce.django import django_url
from django.contrib.auth.models import User
from student.models import CourseEnrollment
from xmodule.modulestore import Location
from xmodule.modulestore.django import _MODULESTORES, modulestore
from xmodule.templates import update_templates
from xmodule.course_module import CourseDescriptor
from courseware.courses import get_course_by_id
from xmodule import seq_module, vertical_module

from logging import getLogger
logger = getLogger(__name__)

TEST_COURSE_ORG = 'edx'
TEST_COURSE_NAME = 'Test Course'
TEST_SECTION_NAME = 'Test Section'


@step(u'The course "([^"]*)" exists$')
def create_course(step, course):

    # First clear the modulestore so we don't try to recreate
    # the same course twice
    # This also ensures that the necessary templates are loaded
    world.clear_courses()

    # Create the course
    # We always use the same org and display name,
    # but vary the course identifier (e.g. 600x or 191x)
    course = world.CourseFactory.create(org=TEST_COURSE_ORG,
                                        number=course,
                                        display_name=TEST_COURSE_NAME)

    # Add a section to the course to contain problems
    section = world.ItemFactory.create(parent_location=course.location,
                                       display_name=TEST_SECTION_NAME)

    problem_section = world.ItemFactory.create(parent_location=section.location,
                                               template='i4x://edx/templates/sequential/Empty',
                                               display_name=TEST_SECTION_NAME)


@step(u'I am registered for the course "([^"]*)"$')
def i_am_registered_for_the_course(step, course):
    # Create the course
    create_course(step, course)

    # Create the user
    world.create_user('robot')
    u = User.objects.get(username='robot')

    # If the user is not already enrolled, enroll the user.
    # TODO: change to factory
    CourseEnrollment.objects.get_or_create(user=u, course_id=course_id(course))

    world.log_in('robot', 'test')


@step(u'The course "([^"]*)" has extra tab "([^"]*)"$')
def add_tab_to_course(step, course, extra_tab_name):
    section_item = world.ItemFactory.create(parent_location=course_location(course),
                                            template="i4x://edx/templates/static_tab/Empty",
                                            display_name=str(extra_tab_name))


def course_id(course_num):
    return "%s/%s/%s" % (TEST_COURSE_ORG, course_num,
                         TEST_COURSE_NAME.replace(" ", "_"))


def course_location(course_num):
    return Location(loc_or_tag="i4x",
                    org=TEST_COURSE_ORG,
                    course=course_num,
                    category='course',
                    name=TEST_COURSE_NAME.replace(" ", "_"))


def section_location(course_num):
    return Location(loc_or_tag="i4x",
                    org=TEST_COURSE_ORG,
                    course=course_num,
                    category='sequential',
                    name=TEST_SECTION_NAME.replace(" ", "_"))


def get_courses():
    '''
    Returns dict of lists of courses available, keyed by course.org (ie university).
    Courses are sorted by course.number.
    '''
    courses = [c for c in modulestore().get_courses()
               if isinstance(c, CourseDescriptor)]
    courses = sorted(courses, key=lambda course: course.number)
    return courses


def get_courseware_with_tabs(course_id):
    """
    Given a course_id (string), return a courseware array of dictionaries for the
    top three levels of navigation. Same as get_courseware() except include
    the tabs on the right hand main navigation page.

    This hides the appropriate courseware as defined by the hide_from_toc field:
    chapter.lms.hide_from_toc

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
            'tab_classes': ['VerticalDescriptor']
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
            'tab_classes': ['VerticalDescriptor', 'VerticalDescriptor', 'VerticalDescriptor', 'VerticalDescriptor']
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
            'tab_classes': ['VerticalDescriptor', 'VerticalDescriptor']
        }]
    }]
    """

    course = get_course_by_id(course_id)
    chapters = [chapter for chapter in course.get_children() if not chapter.lms.hide_from_toc]
    courseware = [{'chapter_name': c.display_name_with_default,
                   'sections': [{'section_name': s.display_name_with_default,
                                'clickable_tab_count': len(s.get_children()) if (type(s) == seq_module.SequenceDescriptor) else 0,
                                'tabs': [{'children_count': len(t.get_children()) if (type(t) == vertical_module.VerticalDescriptor) else 0,
                                         'class': t.__class__.__name__}
                                         for t in s.get_children()]}
                                for s in c.get_children() if not s.lms.hide_from_toc]}
                  for c in chapters]

    return courseware
