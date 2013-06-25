#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from django.contrib.auth.models import User
from lettuce.django import django_url
from student.models import CourseEnrollment
from common import course_id, course_location
from problems_setup import PROBLEM_DICT

TEST_COURSE_ORG = 'edx'
TEST_COURSE_NAME = 'Test Course'
TEST_SECTION_NAME = 'Test Section'
TEST_SUBSECTION_NAME = 'Test Subsection'


@step(u'I am viewing a course with multiple sections')
def view_course_multiple_sections(step):
    create_course()
    # Add a section to the course to contain problems
    section1 = world.ItemFactory.create(parent_location=course_location('model_course'),
                                       display_name=section_name(1))

    # Add a section to the course to contain problems
    section2 = world.ItemFactory.create(parent_location=course_location('model_course'),
                                       display_name=section_name(2))

    place1 = world.ItemFactory.create(parent_location=section1.location,
                                               category='sequential',
                                               display_name=subsection_name(1))

    place2 = world.ItemFactory.create(parent_location=section2.location,
                                               category='sequential',
                                               display_name=subsection_name(2))

    add_problem_to_course_section('model_course', 'multiple choice', place1.location)
    add_problem_to_course_section('model_course', 'drop down', place2.location)

    create_user_and_visit_course()


@step(u'I am viewing a section with multiple subsections')
def view_course_multiple_subsections(step):
    create_course()

    # Add a section to the course to contain problems
    section1 = world.ItemFactory.create(parent_location=course_location('model_course'),
                                       display_name=section_name(1))

    place1 = world.ItemFactory.create(parent_location=section1.location,
                                               category='sequential',
                                               display_name=subsection_name(1))

    place2 = world.ItemFactory.create(parent_location=section1.location,
                                       display_name=subsection_name(2))

    add_problem_to_course_section('model_course', 'multiple choice', place1.location)
    add_problem_to_course_section('model_course', 'drop down', place2.location)

    create_user_and_visit_course()


@step(u'I am viewing a section with multiple sequences')
def view_course_multiple_sequences(step):
    create_course()
    # Add a section to the course to contain problems
    section1 = world.ItemFactory.create(parent_location=course_location('model_course'),
                                       display_name=section_name(1))

    place1 = world.ItemFactory.create(parent_location=section1.location,
                                               category='sequential',
                                               display_name=subsection_name(1))

    add_problem_to_course_section('model_course', 'multiple choice', place1.location)
    add_problem_to_course_section('model_course', 'drop down', place1.location)

    create_user_and_visit_course()


@step(u'I click on section "([^"]*)"$')
def click_on_section(step, section):
    section_css = 'h3[tabindex="-1"]'
    world.css_click(section_css)

    subid = "ui-accordion-accordion-panel-" + str(int(section) - 1)
    subsection_css = 'ul.ui-accordion-content-active[id=\'%s\'] > li > a' % subid
    prev_url = world.browser.url
    changed_section = lambda: prev_url != world.browser.url

    #for some reason needed to do it in two steps
    world.css_click(subsection_css, success_condition=changed_section)


@step(u'I click on subsection "([^"]*)"$')
def click_on_subsection(step, subsection):
    subsection_css = 'ul[id="ui-accordion-accordion-panel-0"]> li > a'
    world.css_click(subsection_css, index=(int(subsection) - 1))


@step(u'I click on sequence "([^"]*)"$')
def click_on_sequence(step, sequence):
    sequence_css = 'a[data-element="%s"]' % sequence
    world.css_click(sequence_css)


@step(u'I should see the content of (?:sub)?section "([^"]*)"$')
def see_section_content(step, section):
    if section == "2":
        text = 'The correct answer is Option 2'
    elif section == "1":
        text = 'The correct answer is Choice 3'
    step.given('I should see "' + text + '" somewhere on the page')


@step(u'I should see the content of sequence "([^"]*)"$')
def see_sequence_content(step, sequence):
    step.given('I should see the content of section "2"')


@step(u'I return later')
def return_to_course(step):
    step.given('I visit the homepage')
    world.click_link("View Course")
    world.click_link("Courseware")


@step(u'I should see that I was most recently in section "([^"]*)"$')
def see_recent_section(step, section):
    step.given('I should see "You were most recently in %s" somewhere on the page' % subsection_name(int(section)))

#####################
#      HELPERS
#####################


def section_name(section):
    return TEST_SECTION_NAME + str(section)


def subsection_name(section):
    return TEST_SUBSECTION_NAME + str(section)


def create_course():
    world.clear_courses()

    world.CourseFactory.create(org=TEST_COURSE_ORG,
                                        number="model_course",
                                        display_name=TEST_COURSE_NAME)


def create_user_and_visit_course():
    world.create_user('robot')
    u = User.objects.get(username='robot')

    CourseEnrollment.objects.get_or_create(user=u, course_id=course_id("model_course"))

    world.log_in('robot', 'test')
    chapter_name = (TEST_SECTION_NAME + "1").replace(" ", "_")
    section_name = (TEST_SUBSECTION_NAME + "1").replace(" ", "_")
    url = django_url('/courses/edx/model_course/Test_Course/courseware/%s/%s' %
                    (chapter_name, section_name))

    world.browser.visit(url)


def add_problem_to_course_section(course, problem_type, parent_location, extraMeta=None):
    '''
    Add a problem to the course we have created using factories.
    '''

    assert(problem_type in PROBLEM_DICT)

    # Generate the problem XML using capa.tests.response_xml_factory
    factory_dict = PROBLEM_DICT[problem_type]
    problem_xml = factory_dict['factory'].build_xml(**factory_dict['kwargs'])
    metadata = {'rerandomize': 'always'} if not 'metadata' in factory_dict else factory_dict['metadata']
    if extraMeta:
        metadata = dict(metadata, **extraMeta)

    # Create a problem item using our generated XML
    # We set rerandomize=always in the metadata so that the "Reset" button
    # will appear.
    world.ItemFactory.create(parent_location=parent_location,
                            category='problem',
                            display_name=str(problem_type),
                            data=problem_xml,
                            metadata=metadata)
