# disable missing docstring
#pylint: disable=C0111

from lettuce import world, step


@step('I have created a Discussion Tag$')
def i_created_discussion_tag(step):
    world.create_component_instance(
        step, '.large-discussion-icon',
        'discussion',
        '.xmodule_DiscussionModule',
        has_multiple_templates=False
    )


@step('I see three alphabetized settings and their expected values$')
def i_see_only_the_settings_and_values(step):
    world.verify_all_setting_entries(
        [
            ['Category', "Week 1", False],
            ['Display Name', "Discussion", False],
            ['Subcategory', "Topic-Level Student-Visible Label", False]
        ])


@step('creating a discussion takes a single click')
def discussion_takes_a_single_click(step):
    assert(not world.is_css_present('.xmodule_DiscussionModule'))
    world.css_click("a[data-category='discussion']")
    assert(world.is_css_present('.xmodule_DiscussionModule'))
