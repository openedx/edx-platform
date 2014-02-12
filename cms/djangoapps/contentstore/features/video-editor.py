# disable missing docstring
# pylint: disable=C0111

from lettuce import world, step
from terrain.steps import reload_the_page


@step('I have set "show transcript" to (.*)$')
def set_show_captions(step, setting):
    # Prevent cookies from overriding course settings
    world.browser.cookies.delete('hide_captions')

    world.css_click('a.edit-button')
    world.wait_for(lambda _driver: world.css_visible('a.save-button'))
    world.click_link_by_text('Advanced')
    world.browser.select('Show Transcript', setting)
    world.css_click('a.save-button')


@step('when I view the video it (.*) show the captions$')
def shows_captions(_step, show_captions):
    world.wait_for_js_variable_truthy("Video")
    world.wait(0.5)
    if show_captions == 'does not':
        assert world.is_css_present('div.video.closed')
    else:
        assert world.is_css_not_present('div.video.closed')

    # Prevent cookies from overriding course settings
    world.browser.cookies.delete('hide_captions')
    world.browser.cookies.delete('current_player_mode')


@step('I see the correct video settings and default values$')
def correct_video_settings(_step):
    expected_entries = [
        # basic
        ['Display Name', 'Video', False],
        ['Video URL', 'http://youtu.be/OEoXaMPEzfM, , ', False],

        # advanced
        ['Display Name', 'Video', False],
        ['Download Transcript', '', False],
        ['End Time', '00:00:00', False],
        ['HTML5 Transcript', '', False],
        ['Show Transcript', 'True', False],
        ['Start Time', '00:00:00', False],
        # ['Transcript Download Allowed', 'False', False],
        ['Video Download Allowed', 'False', False],
        ['Video Sources', '', False],
        ['Youtube ID', 'OEoXaMPEzfM', False],
        ['Youtube ID for .75x speed', '', False],
        ['Youtube ID for 1.25x speed', '', False],
        ['Youtube ID for 1.5x speed', '', False]
    ]
    world.verify_all_setting_entries(expected_entries)


@step('my video display name change is persisted on save$')
def video_name_persisted(step):
    world.css_click('a.save-button')
    reload_the_page(step)
    world.wait_for_xmodule()
    world.edit_component()

    world.verify_setting_entry(
        world.get_setting_entry('Display Name'),
        'Display Name', '3.4', True
    )
