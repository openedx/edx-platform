# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

from lettuce import world, steps
from nose.tools import assert_in, assert_true  # pylint: disable=no-name-in-module

from common import i_am_registered_for_the_course, visit_scenario_item
from problems_setup import add_problem_to_course, answer_problem


@steps
class ConditionalSteps(object):
    COURSE_NUM = 'test_course'

    def setup_conditional(self, step, condition_type, condition, cond_value):
        r'that a course has a Conditional conditioned on (?P<condition_type>\w+) (?P<condition>\w+)=(?P<cond_value>\w+)$'

        i_am_registered_for_the_course(step, self.COURSE_NUM)

        world.scenario_dict['VERTICAL'] = world.ItemFactory(
            parent_location=world.scenario_dict['SECTION'].location,
            category='vertical',
            display_name="Test Vertical",
        )

        world.scenario_dict['WRAPPER'] = world.ItemFactory(
            parent_location=world.scenario_dict['VERTICAL'].location,
            category='wrapper',
            display_name="Test Poll Wrapper"
        )

        if condition_type == 'problem':
            world.scenario_dict['CONDITION_SOURCE'] = add_problem_to_course(self.COURSE_NUM, 'string')
        elif condition_type == 'poll':
            world.scenario_dict['CONDITION_SOURCE'] = world.ItemFactory(
                parent_location=world.scenario_dict['WRAPPER'].location,
                category='poll_question',
                display_name='Conditional Poll',
                data={
                    'question': 'Is this a good poll?',
                    'answers': [
                        {'id': 'yes', 'text': 'Yes, of course'},
                        {'id': 'no', 'text': 'Of course not!'}
                    ],
                }
            )
        else:
            raise Exception("Unknown condition type: {!r}".format(condition_type))

        metadata = {
            'xml_attributes': {
                condition: cond_value
            }
        }

        world.scenario_dict['CONDITIONAL'] = world.ItemFactory(
            parent_location=world.scenario_dict['WRAPPER'].location,
            category='conditional',
            display_name="Test Conditional",
            metadata=metadata,
            sources_list=[world.scenario_dict['CONDITION_SOURCE'].location],
        )

        world.ItemFactory(
            parent_location=world.scenario_dict['CONDITIONAL'].location,
            category='html',
            display_name='Conditional Contents',
            data='<html><div class="hidden-contents">Hidden Contents</p></html>'
        )

    def setup_problem_attempts(self, step, not_attempted=None):
        r'that the conditioned problem has (?P<not_attempted>not )?been attempted$'
        visit_scenario_item('CONDITION_SOURCE')

        if not_attempted is None:
            answer_problem(self.COURSE_NUM, 'string', True)
            world.css_click("button.check")

    def when_i_view_the_conditional(self, step):
        r'I view the conditional$'
        visit_scenario_item('CONDITIONAL')
        world.wait_for_js_variable_truthy('$(".xblock-student_view[data-type=Conditional]").data("initialized")')

    def check_visibility(self, step, visible):
        r'the conditional contents are (?P<visible>\w+)$'
        world.wait_for_ajax_complete()

        assert_in(visible, ('visible', 'hidden'))

        if visible == 'visible':
            world.wait_for_visible('.hidden-contents')
            assert_true(world.css_visible('.hidden-contents'))
        else:
            assert_true(world.is_css_not_present('.hidden-contents'))
            assert_true(
                world.css_contains_text(
                    '.conditional-message',
                    'must be attempted before this will become visible.'
                )
            )

    def answer_poll(self, step, answer):
        r' I answer the conditioned poll "([^"]*)"$'
        visit_scenario_item('CONDITION_SOURCE')
        world.wait_for_js_variable_truthy('$(".xblock-student_view[data-type=Poll]").data("initialized")')
        world.wait_for_ajax_complete()

        answer_text = [
            poll_answer['text']
            for poll_answer
            in world.scenario_dict['CONDITION_SOURCE'].answers
            if poll_answer['id'] == answer
        ][0]

        text_selector = '.poll_answer .text'

        poll_texts = world.retry_on_exception(
            lambda: [elem.text for elem in world.css_find(text_selector)]
        )

        for idx, poll_text in enumerate(poll_texts):
            if poll_text == answer_text:
                world.css_click(text_selector, index=idx)
                return


ConditionalSteps()
