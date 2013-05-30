# disable missing docstring
#pylint: disable=C0111

from lettuce import world, step


@step('I have created a Discussion Tag$')
def i_created_discussion_tag(step):
    world.create_component_instance(
        step, '.large-discussion-icon',
        'i4x://edx/templates/discussion/Discussion_Tag',
        '.xmodule_DiscussionModule'
    )


@step('I see three alphabetized settings and their expected values$')
def i_see_only_the_settings_and_values(step):
    world.verify_all_setting_entries(
        [
            ['Category', "Week 1", True],
            ['Display Name', "Discussion Tag", True],
            ['Subcategory', "Topic-Level Student-Visible Label", True]
        ])
