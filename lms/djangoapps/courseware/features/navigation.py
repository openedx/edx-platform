#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from django.contrib.auth.models import User
from lettuce.django import django_url
from student.models import CourseEnrollment
from common import course_id
from xmodule.modulestore import Location
from problems_setup import PROBLEM_DICT

TEST_COURSE_ORG = 'edx'
TEST_COURSE_NAME = 'Test Course'
TEST_SECTION_NAME = 'Test Section'
SUBSECTION_2_LOC = None


@step(u'I am viewing a course with multiple sections')
def view_course_multiple_sections(step):
    # First clear the modulestore so we don't try to recreate
    # the same course twice
    # This also ensures that the necessary templates are loaded
    world.clear_courses()

    # Create the course
    # We always use the same org and display name,
    # but vary the course identifier (e.g. 600x or 191x)
    course = world.CourseFactory.create(org=TEST_COURSE_ORG,
                                        number="model_course",
                                        display_name=TEST_COURSE_NAME)

    # Add a section to the course to contain problems
    section1 = world.ItemFactory.create(parent_location=course.location,
                                       display_name=TEST_SECTION_NAME+"1")

    # Add a section to the course to contain problems
    section2 = world.ItemFactory.create(parent_location=course.location,
                                       display_name=TEST_SECTION_NAME+"2")

    world.ItemFactory.create(parent_location=section1.location,
                                               template='i4x://edx/templates/sequential/Empty',
                                               display_name=TEST_SECTION_NAME+"1")

    world.ItemFactory.create(parent_location=section2.location,
                                               template='i4x://edx/templates/sequential/Empty',
                                               display_name=TEST_SECTION_NAME+"2")

    add_problem_to_course_section('model_course', 'multiple choice', section=1)
    add_problem_to_course_section('model_course', 'drop down', section=2)

    # Create the user
    world.create_user('robot')
    u = User.objects.get(username='robot')

    # If the user is not already enrolled, enroll the user.
    # TODO: change to factory
    CourseEnrollment.objects.get_or_create(user=u, course_id=course_id("model_course"))

    world.log_in('robot', 'test')
    chapter_name = (TEST_SECTION_NAME+"1").replace(" ", "_")
    section_name = chapter_name
    url = django_url('/courses/edx/model_course/Test_Course/courseware/%s/%s' %
                    (chapter_name, section_name))

    world.browser.visit(url)


@step(u'I am viewing a section with multiple subsections')
def view_course_multiple_subsections(step):
        # First clear the modulestore so we don't try to recreate
    # the same course twice
    # This also ensures that the necessary templates are loaded
    world.clear_courses()

    # Create the course
    # We always use the same org and display name,
    # but vary the course identifier (e.g. 600x or 191x)
    course = world.CourseFactory.create(org=TEST_COURSE_ORG,
                                        number="model_course",
                                        display_name=TEST_COURSE_NAME)

    # Add a section to the course to contain problems
    section1 = world.ItemFactory.create(parent_location=course.location,
                                       display_name=TEST_SECTION_NAME+"1")

    world.ItemFactory.create(parent_location=section1.location,
                                               template='i4x://edx/templates/sequential/Empty',
                                               display_name=TEST_SECTION_NAME+"1")

    section2 = world.ItemFactory.create(parent_location=section1.location,
                                       display_name=TEST_SECTION_NAME+"2")

    global SUBSECTION_2_LOC
    SUBSECTION_2_LOC = section2.location


    add_problem_to_course_section('model_course', 'multiple choice', section=1)
    add_problem_to_course_section('model_course', 'drop down', section=1, subsection=2)

    # Create the user
    world.create_user('robot')
    u = User.objects.get(username='robot')

    # If the user is not already enrolled, enroll the user.
    # TODO: change to factory
    CourseEnrollment.objects.get_or_create(user=u, course_id=course_id("model_course"))

    world.log_in('robot', 'test')
    chapter_name = (TEST_SECTION_NAME+"1").replace(" ", "_")
    section_name = chapter_name
    url = django_url('/courses/edx/model_course/Test_Course/courseware/%s/%s' %
                    (chapter_name, section_name))

    world.browser.visit(url)


@step(u'I am viewing a section with multiple sequences')
def view_course_multiple_sequences(step):
        # First clear the modulestore so we don't try to recreate
    # the same course twice
    # This also ensures that the necessary templates are loaded
    world.clear_courses()

    # Create the course
    # We always use the same org and display name,
    # but vary the course identifier (e.g. 600x or 191x)
    course = world.CourseFactory.create(org=TEST_COURSE_ORG,
                                        number="model_course",
                                        display_name=TEST_COURSE_NAME)

    # Add a section to the course to contain problems
    section1 = world.ItemFactory.create(parent_location=course.location,
                                       display_name=TEST_SECTION_NAME+"1")


    world.ItemFactory.create(parent_location=section1.location,
                                               template='i4x://edx/templates/sequential/Empty',
                                               display_name=TEST_SECTION_NAME+"1")

    add_problem_to_course_section('model_course', 'multiple choice', section=1)
    add_problem_to_course_section('model_course', 'drop down', section=1)

    # Create the user
    world.create_user('robot')
    u = User.objects.get(username='robot')

    # If the user is not already enrolled, enroll the user.
    # TODO: change to factory
    CourseEnrollment.objects.get_or_create(user=u, course_id=course_id("model_course"))

    world.log_in('robot', 'test')
    chapter_name = (TEST_SECTION_NAME+"1").replace(" ", "_")
    section_name = chapter_name
    url = django_url('/courses/edx/model_course/Test_Course/courseware/%s/%s' %
                    (chapter_name, section_name))

    world.browser.visit(url)


@step(u'I click on section "([^"]*)"')
def click_on_section(step, section):
    section_css = 'h3[tabindex="-1"]'
    elist = world.css_find(section_css)
    assert not elist.is_empty()
    elist.click()
    subid = "ui-accordion-accordion-panel-"+str(int(section)-1)
    subsection_css = 'ul[id="%s"]>li[class=" "] a' % subid
    elist = world.css_find(subsection_css)
    assert not elist.is_empty()
    elist.click()


@step(u'I click on subsection "([^"]*)"')
def click_on_subsection(step, subsection):
    subsection_css = 'ul[id="ui-accordion-accordion-panel-0"]>li[class=" "] a'
    elist = world.css_find(subsection_css)
    assert not elist.is_empty()
    elist.click()

@step(u'I click on sequence "([^"]*)"')
def click_on_subsection(step, sequence):
    sequence_css = 'a[data-element="%s"]' % sequence
    elist = world.css_find(sequence_css)
    assert not elist.is_empty()
    elist.click()


@step(u'I see the content of (?:sub)?section "([^"]*)"')
def see_section_content(step, section):
    if section == "2":
        text = 'The correct answer is Option 2'
    elif section == "1":
        text = 'The correct answer is Choice 3'
    step.given('I should see "' + text + '" somewhere on the page')


@step(u'I see the content of sequence "([^"]*)"')
def see_sequence_content(step, sequence):
    step.given('I see the content of section "2"')


@step(u'I go to the section')
def return_to_course(step):
    world.click_link("View Course")
    world.click_link("Courseware")

###
#HELPERS
###


def add_problem_to_course_section(course, problem_type, extraMeta=None, section=1, subsection=1):
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
    template_name = "i4x://edx/templates/problem/Blank_Common_Problem"
    world.ItemFactory.create(parent_location=section_location(course, section) if subsection == 1 else SUBSECTION_2_LOC,
                            template=template_name,
                            display_name=str(problem_type),
                            data=problem_xml,
                            metadata=metadata)


def section_location(course_num, section_num):
    return Location(loc_or_tag="i4x",
                    org=TEST_COURSE_ORG,
                    course=course_num,
                    category='sequential',
                    name=(TEST_SECTION_NAME+str(section_num)).replace(" ", "_"))
