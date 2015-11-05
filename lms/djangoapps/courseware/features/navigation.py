# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

from lettuce import world, step
from common import course_location
from problems_setup import PROBLEM_DICT
from nose.tools import assert_in


@step(u'I am viewing a course with multiple sections')
def view_course_multiple_sections(step):
    create_course()

    section1 = world.ItemFactory.create(
        parent_location=course_location(world.scenario_dict['COURSE'].number),
        display_name="Test Section 1"
    )

    section2 = world.ItemFactory.create(
        parent_location=course_location(world.scenario_dict['COURSE'].number),
        display_name="Test Section 2"
    )

    place1 = world.ItemFactory.create(
        parent_location=section1.location,
        category='sequential',
        display_name="Test Subsection 1"
    )

    place2 = world.ItemFactory.create(
        parent_location=section2.location,
        category='sequential',
        display_name="Test Subsection 2"
    )

    add_problem_to_course_section(place1.location, "Problem 1")
    add_problem_to_course_section(place2.location, "Problem 2")

    create_user_and_visit_course()


@step(u'I am viewing a section with multiple subsections')
def view_course_multiple_subsections(step):
    create_course()

    section1 = world.ItemFactory.create(
        parent_location=course_location(world.scenario_dict['COURSE'].number),
        display_name="Test Section 1"
    )

    place1 = world.ItemFactory.create(
        parent_location=section1.location,
        category='sequential',
        display_name="Test Subsection 1"
    )

    place2 = world.ItemFactory.create(
        parent_location=section1.location,
        display_name="Test Subsection 2"
    )

    add_problem_to_course_section(place1.location, "Problem 3")
    add_problem_to_course_section(place2.location, "Problem 4")

    create_user_and_visit_course()


@step(u'I am viewing a section with multiple sequences')
def view_course_multiple_sequences(step):
    create_course()

    section1 = world.ItemFactory.create(
        parent_location=course_location(world.scenario_dict['COURSE'].number),
        display_name="Test Section 1"
    )

    place1 = world.ItemFactory.create(
        parent_location=section1.location,
        category='sequential',
        display_name="Test Subsection 1"
    )

    add_problem_to_course_section(place1.location, "Problem 5")
    add_problem_to_course_section(place1.location, "Problem 6")

    create_user_and_visit_course()


@step(u'I navigate to a section')
def when_i_navigate_to_a_section(step):
    # Prevent jQuery menu animations from interferring with the clicks
    world.disable_jquery_animations()

    # Open the 2nd section
    world.css_click(css_selector='.chapter', index=1)
    subsection_css = 'a[href*="Test_Subsection_2/"]'

    # Click on the subsection to see the content
    world.css_click(subsection_css)


@step(u'I navigate to a subsection')
def when_i_navigate_to_a_subsection(step):
    # Click on the 2nd subsection to see the content
    subsection_css = 'a[href*="Test_Subsection_2/"]'
    world.css_click(subsection_css)


@step(u'I navigate to an item in a sequence')
def when_i_navigate_to_an_item_in_a_sequence(step):
    sequence_css = 'a[data-element="2"]'
    world.css_click(sequence_css)


@step(u'I see the content of the section')
def then_i_see_the_content_of_the_section(step):
    wait_for_problem('Problem 2')


@step(u'I see the content of the subsection')
def then_i_see_the_content_of_the_subsection(step):
    wait_for_problem('Problem 4')


@step(u'I see the content of the sequence item')
def then_i_see_the_content_of_the_sequence_item(step):
    wait_for_problem('Problem 6')


@step(u'I return to the course')
def and_i_return_to_the_course(step):
    world.visit('/')
    world.click_link("View Course")
    course = 'a[href*="/courseware"]'
    world.css_click(course)


def create_course():
    world.clear_courses()
    world.scenario_dict['COURSE'] = world.CourseFactory.create(
        org='edx', number='999', display_name='Test Course'
    )


def create_user_and_visit_course():
    world.register_by_course_key(world.scenario_dict['COURSE'].id)
    world.log_in()
    world.visit(u'/courses/{}/courseware/'.format(world.scenario_dict['COURSE'].id))


def add_problem_to_course_section(parent_location, display_name):
    """
    Add a problem to the course at `parent_location` (a `Location` instance)

    `display_name` is the name of the problem to display, which
    is useful to identify which problem we're looking at.
    """

    # Generate the problem XML using capa.tests.response_xml_factory
    # Since this is just a placeholder, we always use multiple choice.
    factory_dict = PROBLEM_DICT['multiple choice']
    problem_xml = factory_dict['factory'].build_xml(**factory_dict['kwargs'])

    # Add the problem
    world.ItemFactory.create(
        parent_location=parent_location,
        category='problem',
        display_name=display_name,
        data=problem_xml
    )


def wait_for_problem(display_name):
    """
    Wait for the problem with `display_name` to appear on the page.
    """
    # Wait for the problem to reload
    world.wait_for_ajax_complete()

    wait_func = lambda _: world.css_has_text(
        '.problem-header', display_name, strip=True
    )
    world.wait_for(wait_func)
