#pylint: disable=C0111

from lettuce import world, step

############### ACTIONS ####################


@step('when I view the video it does not have autoplay enabled')
def does_not_autoplay(_step):
    assert world.css_find('.video')[0]['data-autoplay'] == 'False'
    assert world.css_find('.video_control')[0].has_class('play')


@step('creating a video takes a single click')
def video_takes_a_single_click(_step):
    assert(not world.is_css_present('.xmodule_VideoModule'))
    world.css_click("a[data-location='i4x://edx/templates/video/default']")
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
