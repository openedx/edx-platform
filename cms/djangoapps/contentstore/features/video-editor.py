#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step


@step('I have created a Video component$')
def i_created_a_video_component(step):
    world.create_component_instance(
        step, '.large-video-icon', 'i4x://edx/templates/video/default',
        '.xmodule_VideoModule'
    )


@step('I see only the video display name setting$')
def i_see_only_the_video_display_name(step):
    world.verify_all_setting_entries([['Display Name', "default", True]])
