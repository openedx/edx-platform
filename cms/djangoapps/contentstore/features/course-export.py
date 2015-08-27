# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

from lettuce import world, step
from component_settings_editor_helpers import enter_xml_in_advanced_problem
from nose.tools import assert_true, assert_equal
from contentstore.utils import reverse_usage_url


@step('I go to the export page$')
def i_go_to_the_export_page(step):
    world.click_tools()
    link_css = 'li.nav-course-tools-export a'
    world.css_click(link_css)


@step('I export the course$')
def i_export_the_course(step):
    step.given('I go to the export page')
    world.css_click('a.action-export')


@step('I edit and enter bad XML$')
def i_enter_bad_xml(step):
    enter_xml_in_advanced_problem(
        step,
        """<problem><h1>Smallest Canvas</h1>
            <p>You want to make the smallest canvas you can.</p>
            <multiplechoiceresponse>
            <choicegroup type="MultipleChoice">
              <choice correct="false"><verbatim><canvas id="myCanvas" width = 10 height = 100> </canvas></verbatim></choice>
              <choice correct="true"><code><canvas id="myCanvas" width = 10 height = 10> </canvas></code></choice>
            </choicegroup>
            </multiplechoiceresponse>
            </problem>"""
    )


@step('I edit and enter an ampersand$')
def i_enter_an_ampersand(step):
    enter_xml_in_advanced_problem(step, "<problem>&</problem>")


@step('I get an error dialog$')
def get_an_error_dialog(step):
    assert_true(world.is_css_present("div.prompt.error"))


@step('I can click to go to the unit with the error$')
def i_click_on_error_dialog(step):
    world.css_click("button.action-primary")

    problem_string = unicode(world.scenario_dict['COURSE'].id.make_usage_key("problem", 'ignore'))
    problem_string = u"Problem {}".format(problem_string[:problem_string.rfind('ignore')])
    assert_true(
        world.css_html("span.inline-error").startswith(problem_string),
        u"{} does not start with {}".format(
            world.css_html("span.inline-error"), problem_string
        ))
    # we don't know the actual ID of the vertical. So just check that we did go to a
    # vertical page in the course (there should only be one).
    vertical_usage_key = world.scenario_dict['COURSE'].id.make_usage_key("vertical", "test")
    vertical_url = reverse_usage_url('container_handler', vertical_usage_key)
    # Remove the trailing "/None" from the URL - we don't know the course ID, so we just want to
    # check that we visited a vertical URL.
    if vertical_url.endswith("/test") or vertical_url.endswith("@test"):
        vertical_url = vertical_url[:-5]
    assert_equal(1, world.browser.url.count(vertical_url))
