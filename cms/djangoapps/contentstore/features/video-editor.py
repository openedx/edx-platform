# disable missing docstring
#pylint: disable=C0111

from lettuce import world, step


@step('I see only the video display name setting$')
def i_see_only_the_video_display_name(step):
    world.verify_all_setting_entries([['Display Name', "default", True]])
