import textwrap

from lettuce import world, steps
from nose.tools import assert_in, assert_equals

from common import i_am_registered_for_the_course, visit_scenario_item

DATA_TEMPLATE = textwrap.dedent("""\
    <annotatable>
        <instructions>Instruction text</instructions>
        <p>{}</p>
    </annotatable>
""")

ANNOTATION_TEMPLATE = textwrap.dedent("""\
    Before {0}.
    <annotation title="region {0}" body="Comment {0}" highlight="yellow" problem="{0}">
        Region Contents {0}
    </annotation>
    After {0}.
""")

PROBLEM_TEMPLATE = textwrap.dedent("""\
<problem max_attempts="1" weight="">
  <annotationresponse>
    <annotationinput>
      <title>Question {number}</title>
      <text>Region Contents {number}</text>
      <comment>What number is this region?</comment>
      <comment_prompt>Type your response below:</comment_prompt>
      <tag_prompt>What number is this region?</tag_prompt>
      <options>
      {options}
      </options>
    </annotationinput>
  </annotationresponse>
  <solution>
    This problem is checking region {number}
  </solution>
</problem>
""")

OPTION_TEMPLATE = """<option choice="{correctness}">{number}</option>"""


def _correctness(choice, target):
    if choice == target:
        return "correct"
    elif abs(choice - target) == 1:
        return "partially-correct"
    else:
        return "incorrect"


@steps
class AnnotatableSteps(object):

    def __init__(self):
        self.annotations_count = None
        self.active_problem = None

    def define_component(self, step, count):
        r"""that a course has an annotatable component with (?P<count>\d+) annotations$"""

        count = int(count)
        coursenum = 'test_course'
        i_am_registered_for_the_course(step, coursenum)

        world.scenario_dict['ANNOTATION_VERTICAL'] = world.ItemFactory(
            parent_location=world.scenario_dict['SECTION'].location,
            category='vertical',
            display_name="Test Annotation Vertical"
        )

        world.scenario_dict['ANNOTATABLE'] = world.ItemFactory(
            parent_location=world.scenario_dict['ANNOTATION_VERTICAL'].location,
            category='annotatable',
            display_name="Test Annotation Module",
            data=DATA_TEMPLATE.format("\n".join(ANNOTATION_TEMPLATE.format(i) for i in xrange(count)))
        )
        self.annotations_count = count

    def view_component(self, step):
        r"""I view the annotatable component$"""
        visit_scenario_item('ANNOTATABLE')

    def check_rendered(self, step):
        r"""the annotatable component has rendered$"""
        world.wait_for_js_variable_truthy('$(".xblock-student_view[data-type=Annotatable]").data("initialized")')
        annotatable_text = world.css_find('.xblock-student_view[data-type=Annotatable]').first.text
        assert_in("Instruction text", annotatable_text)

        for i in xrange(self.annotations_count):
            assert_in("Region Contents {}".format(i), annotatable_text)

    def count_passages(self, step, count):
        r"""the annotatable component has (?P<count>\d+) highlighted passages$"""
        count = int(count)
        assert_equals(len(world.css_find('.annotatable-span')), count)
        assert_equals(len(world.css_find('.annotatable-span.highlight')), count)
        assert_equals(len(world.css_find('.annotatable-span.highlight-yellow')), count)

# This line is required by @steps in order to actually bind the step
# regexes
AnnotatableSteps()
