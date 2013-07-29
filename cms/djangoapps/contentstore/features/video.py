#pylint: disable=C0111

from lettuce import world, step
from terrain.steps import reload_the_page

############### ACTIONS ####################


@step('when I view the (.*) it does not have autoplay enabled')
def does_not_autoplay(_step, video_type):
    assert world.css_find('.%s' % video_type)[0]['data-autoplay'] == 'False'
    assert world.css_has_class('.video_control', 'play')


@step('creating a video takes a single click')
def video_takes_a_single_click(_step):
    assert(not world.is_css_present('.xmodule_VideoModule'))
    world.css_click("a[data-category='video']")
    assert(world.is_css_present('.xmodule_VideoModule'))


@step('I have (hidden|toggled) captions')
def hide_or_show_captions(step, shown):
    button_css = 'a.hide-subtitles'
    if shown == 'hidden':
        world.css_click(button_css)
    if shown == 'toggled':
        world.css_click(button_css)
        # When we click the first time, a tooltip shows up. We want to
        # click the button rather than the tooltip, so move the mouse
        # away to make it disappear.
        button = world.css_find(button_css)
        button.mouse_out()
        world.css_click(button_css)

@step('I edit the component')
def i_edit_the_component(_step):
    world.edit_component()


@step('my videoalpha display name change is persisted on save')
def videoalpha_name_persisted(step):
    world.css_click('a.save-button')
    reload_the_page(step)
    world.edit_component()
    world.verify_setting_entry(world.get_setting_entry('Display Name'), 'Display Name', '3.4', True)
