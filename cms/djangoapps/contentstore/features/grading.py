# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

from lettuce import world, step
from common import *
from terrain.steps import reload_the_page
from selenium.common.exceptions import InvalidElementStateException
from contentstore.utils import reverse_course_url
from nose.tools import assert_in, assert_equal, assert_not_equal


@step(u'I am viewing the grading settings')
def view_grading_settings(step):
    world.click_course_settings()
    link_css = 'li.nav-course-settings-grading a'
    world.css_click(link_css)


@step(u'I add "([^"]*)" new grade')
def add_grade(step, many):
    grade_css = '.new-grade-button'
    for __ in range(int(many)):
        world.css_click(grade_css)


@step(u'I delete a grade')
def delete_grade(step):
    #grade_css = 'li.grade-specific-bar > a.remove-button'
    #range_css = '.grade-specific-bar'
    #world.css_find(range_css)[1].mouseover()
    #world.css_click(grade_css)
    world.browser.execute_script('document.getElementsByClassName("remove-button")[0].click()')


@step(u'Grade list has "([^"]*)" grades$')
def check_grade_values(step, grade_list):  # pylint: disable=unused-argument
    visible_list = ''.join(
        [grade.text for grade in world.css_find('.letter-grade')]
    )
    assert_equal(visible_list, grade_list, 'Grade lists should be equal')


@step(u'I see I now have "([^"]*)" grades$')
def view_grade_slider(step, how_many):
    grade_slider_css = '.grade-specific-bar'
    all_grades = world.css_find(grade_slider_css)
    assert_equal(len(all_grades), int(how_many))


@step(u'I move a grading section')
def move_grade_slider(step):
    moveable_css = '.ui-resizable-e'
    f = world.css_find(moveable_css).first
    f.action_chains.drag_and_drop_by_offset(f._element, 100, 0).perform()


@step(u'I see that the grade range has changed')
def confirm_change(step):
    range_css = '.range'
    all_ranges = world.css_find(range_css)
    for i in range(len(all_ranges)):
        assert_not_equal(world.css_html(range_css, index=i), '0-50')


@step(u'I change assignment type "([^"]*)" to "([^"]*)"$')
def change_assignment_name(step, old_name, new_name):
    name_id = '#course-grading-assignment-name'
    index = get_type_index(old_name)
    f = world.css_find(name_id)[index]
    assert_not_equal(index, -1)
    for __ in xrange(len(old_name)):
        f._element.send_keys(Keys.END, Keys.BACK_SPACE)
    f._element.send_keys(new_name)


@step(u'I go back to the main course page')
def main_course_page(step):
    main_page_link = reverse_course_url('course_handler', world.scenario_dict['COURSE'].id)

    world.visit(main_page_link)
    assert_in('Course Outline', world.css_text('h1.page-header'))


@step(u'I do( not)? see the assignment name "([^"]*)"$')
def see_assignment_name(step, do_not, name):
    # TODO: rewrite this once grading has been added back to the course outline
    pass
    # assignment_menu_css = 'ul.menu > li > a'
    # # First assert that it is there, make take a bit to redraw
    # assert_true(
    #     world.css_find(assignment_menu_css),
    #     msg="Could not find assignment menu"
    # )
    #
    # assignment_menu = world.css_find(assignment_menu_css)
    # allnames = [item.html for item in assignment_menu]
    # if do_not:
    #     assert_not_in(name, allnames)
    # else:
    #     assert_in(name, allnames)


@step(u'I delete the assignment type "([^"]*)"$')
def delete_assignment_type(step, to_delete):
    delete_css = '.remove-grading-data'
    world.css_click(delete_css, index=get_type_index(to_delete))


@step(u'I add a new assignment type "([^"]*)"$')
def add_assignment_type(step, new_name):
    add_button_css = '.add-grading-data'
    world.css_click(add_button_css)
    name_id = '#course-grading-assignment-name'
    new_assignment = world.css_find(name_id)[-1]
    new_assignment._element.send_keys(new_name)


@step(u'I set the assignment weight to "([^"]*)"$')
def set_weight(step, weight):
    weight_id = '#course-grading-assignment-gradeweight'
    weight_field = world.css_find(weight_id)[-1]
    old_weight = world.css_value(weight_id, -1)
    for __ in range(len(old_weight)):
        weight_field._element.send_keys(Keys.END, Keys.BACK_SPACE)
    weight_field._element.send_keys(weight)


@step(u'the assignment weight is displayed as "([^"]*)"$')
def verify_weight(step, weight):
    weight_id = '#course-grading-assignment-gradeweight'
    assert_equal(world.css_value(weight_id, -1), weight)


@step(u'I do not see the changes persisted on refresh$')
def changes_not_persisted(step):
    reload_the_page(step)
    name_id = '#course-grading-assignment-name'
    assert_equal(world.css_value(name_id), 'Homework')


@step(u'I see the assignment type "(.*)"$')
def i_see_the_assignment_type(_step, name):
    assignment_css = '#course-grading-assignment-name'
    assignments = world.css_find(assignment_css)
    types = [ele['value'] for ele in assignments]
    assert_in(name, types)


@step(u'I change the highest grade range to "(.*)"$')
def change_grade_range(_step, range_name):
    range_css = 'span.letter-grade'
    grade = world.css_find(range_css).first
    grade.value = range_name


@step(u'I see the highest grade range is "(.*)"$')
def i_see_highest_grade_range(_step, range_name):
    range_css = 'span.letter-grade'
    grade = world.css_find(range_css).first
    assert_equal(grade.value, range_name)


@step(u'I cannot edit the "Fail" grade range$')
def cannot_edit_fail(_step):
    range_css = 'span.letter-grade'
    ranges = world.css_find(range_css)
    assert_equal(len(ranges), 2)
    assert_not_equal(ranges.last.value, 'Failure')

    # try to change the grade range -- this should throw an exception
    try:
        ranges.last.value = 'Failure'
    except InvalidElementStateException:
        pass  # We should get this exception on failing to edit the element

    # check to be sure that nothing has changed
    ranges = world.css_find(range_css)
    assert_equal(len(ranges), 2)
    assert_not_equal(ranges.last.value, 'Failure')


@step(u'I change the grace period to "(.*)"$')
def i_change_grace_period(_step, grace_period):
    grace_period_css = '#course-grading-graceperiod'
    ele = world.css_find(grace_period_css).first

    # Sometimes it takes a moment for the JavaScript
    # to populate the field.  If we don't wait for
    # this to happen, then we can end up with
    # an invalid value (e.g. "00:0048:00")
    # which prevents us from saving.
    assert_true(world.css_has_value(grace_period_css, "00:00"))

    # Set the new grace period
    ele.value = grace_period


@step(u'I see the grace period is "(.*)"$')
def the_grace_period_is(_step, grace_period):
    grace_period_css = '#course-grading-graceperiod'

    # The default value is 00:00
    # so we need to wait for it to change
    world.wait_for(
        lambda _: world.css_has_value(grace_period_css, grace_period)
    )


def get_type_index(name):
    name_id = '#course-grading-assignment-name'
    all_types = world.css_find(name_id)
    for index in range(len(all_types)):
        if world.css_value(name_id, index=index) == name:
            return index
    return -1
