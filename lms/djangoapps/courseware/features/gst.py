
from lettuce import world, steps
from nose.tools import assert_in, assert_equals, assert_true

from common import i_am_registered_for_the_course, visit_scenario_item
from problems_setup import add_problem_to_course, answer_problem


DEFAULT_DATA = """\
<render>
    <p>Test of the graphical slider tool</p>
    <div class='gst-value'>
        <span id="value-display" style="width:50px; float:left; margin-left:10px;"/>
    </div>
    <div class='gst-input'>
        <slider var="a" style="width:400px;float:left;margin-left:10px;"/>
    </div>
</render>
<configuration>
    <parameters>
        <param var="a" min="0" max="10" step="1" initial="0"/>
    </parameters>
    <functions>
        <function output="element" el_id="value-display">a</function>
    </functions>
</configuration>
"""


@steps
class GraphicalSliderToolSteps(object):
    COURSE_NUM = 'test_course'

    def setup_gst(self, step):
        r'that I have a course with a Graphical Slider Tool$'

        i_am_registered_for_the_course(step, self.COURSE_NUM)

        world.scenario_dict['GST'] = world.ItemFactory(
            parent_location=world.scenario_dict['SECTION'].location,
            category='graphical_slider_tool',
            display_name="Test GST",
            data=DEFAULT_DATA
        )

    def view_gst(self, step):
        r'I view the Graphical Slider Tool$'
        visit_scenario_item('GST')
        world.wait_for_js_variable_truthy('$(".xblock-student_view[data-type=GraphicalSliderTool]").data("initialized")')
        world.wait_for_ajax_complete()

    def check_value(self, step, value):
        r'the displayed value should be (?P<value>\d+)$'

        assert_equals(world.css_text('.gst-value'), value)

    def move_slider(self, step):
        r'I move the slider to the right$'

        handle_selector = '.gst-input .ui-slider-handle'
        world.wait_for_visible(handle_selector)
        world.wait_for_visible('.gst-value #value-display')

        def try_move():
            handle = world.css_find(handle_selector).first
            slider = world.css_find('.gst-input .ui-slider').first
            (handle.action_chains
                .click_and_hold(handle._element)
                .move_by_offset(
                    int(handle._element.location['x'] + 400),
                    0
                ).release().perform())

        world.retry_on_exception(try_move)


GraphicalSliderToolSteps()
