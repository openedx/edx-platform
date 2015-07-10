# pylint: disable=missing-docstring

from lettuce import world, step
from common import i_am_registered_for_the_course, section_location, visit_scenario_item


@step('I view the word cloud and it has rendered')
def word_cloud_is_rendered(_step):
    assert world.is_css_present('.word_cloud')


@step('the course has a Word Cloud component')
def view_word_cloud(_step):
    coursenum = 'test_course'
    i_am_registered_for_the_course(_step, coursenum)

    add_word_cloud_to_course(coursenum)
    visit_scenario_item('SECTION')


@step('I press the Save button')
def press_the_save_button(_step):
    button_css = '.input_cloud_section input.save'
    world.css_click(button_css)


@step('I see the empty result')
def see_empty_result(_step):
    assert world.css_text('.your_words', 0) == ''


@step('I fill inputs')
def fill_inputs(_step):
    input_css = '.input_cloud_section .input-cloud'
    world.css_fill(input_css, 'text1', 0)

    for index in range(1, 4):
        world.css_fill('.input_cloud_section .input-cloud', 'text2', index)


@step('I see the result with words count')
def see_result(_step):
    strong_css = '.your_words strong'
    target_text = set([world.css_text(strong_css, i) for i in range(2)])
    assert set(['text1', 'text2']) == target_text


def add_word_cloud_to_course(course):
    category = 'word_cloud'
    world.ItemFactory.create(parent_location=section_location(course),
                             category=category,
                             display_name='Word Cloud')
