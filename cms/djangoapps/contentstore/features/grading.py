#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from common import *
from terrain.steps import reload_the_page


@step(u'I am viewing the grading settings')
def view_grading_settings(step):
    world.click_course_settings()
    link_css = 'li.nav-course-settings-grading a'
    world.css_click(link_css)


@step(u'I add "([^"]*)" new grade')
def add_grade(step, many):
    grade_css = '.new-grade-button'
    for i in range(int(many)):
        world.css_click(grade_css)


@step(u'I delete a grade')
def delete_grade(step):
    #grade_css = 'li.grade-specific-bar > a.remove-button'
    #range_css = '.grade-specific-bar'
    #world.css_find(range_css)[1].mouseover()
    #world.css_click(grade_css)
    world.browser.execute_script('document.getElementsByClassName("remove-button")[0].click()')


@step(u'I see I now have "([^"]*)" grades$')
def view_grade_slider(step, how_many):
    grade_slider_css = '.grade-specific-bar'
    all_grades = world.css_find(grade_slider_css)
    assert len(all_grades) == int(how_many)


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
        assert world.css_html(range_css, index=i) != '0-50'


@step(u'I change assignment type "([^"]*)" to "([^"]*)"$')
def change_assignment_name(step, old_name, new_name):
    name_id = '#course-grading-assignment-name'
    index = get_type_index(old_name)
    f = world.css_find(name_id)[index]
    assert index != -1
    for count in range(len(old_name)):
        f._element.send_keys(Keys.END, Keys.BACK_SPACE)
    f._element.send_keys(new_name)


@step(u'I go back to the main course page')
def main_course_page(step):
    main_page_link_css = 'a[href="/%s/%s/course/%s"]' % (world.scenario_dict['COURSE'].org,
                                                        world.scenario_dict['COURSE'].number,
                                                        world.scenario_dict['COURSE'].display_name.replace(' ', '_'),)
    world.css_click(main_page_link_css)


@step(u'I do( not)? see the assignment name "([^"]*)"$')
def see_assignment_name(step, do_not, name):
    assignment_menu_css = 'ul.menu > li > a'
    assignment_menu = world.css_find(assignment_menu_css)
    allnames = [item.html for item in assignment_menu]
    if do_not:
        assert not name in allnames
    else:
        assert name in allnames


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


@step(u'I have populated the course')
def populate_course(step):
    step.given('I have added a new section')
    step.given('I have added a new subsection')


@step(u'I do not see the changes persisted on refresh$')
def changes_not_persisted(step):
    reload_the_page(step)
    name_id = '#course-grading-assignment-name'
    assert(world.css_value(name_id) == 'Homework')


@step(u'I see the assignment type "(.*)"$')
def i_see_the_assignment_type(_step, name):
      assignment_css = '#course-grading-assignment-name'
      assignments = world.css_find(assignment_css)
      types = [ele['value'] for ele in assignments]
      assert name in types


def get_type_index(name):
    name_id = '#course-grading-assignment-name'
    all_types = world.css_find(name_id)
    for index in range(len(all_types)):
        if world.css_value(name_id, index=index) == name:
            return index
    return -1
