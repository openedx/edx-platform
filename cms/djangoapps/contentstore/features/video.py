#pylint: disable=C0111

from lettuce import world, step

############### ACTIONS ####################


@step('when I view the video it does not have autoplay enabled')
def does_not_autoplay(step):
    assert world.css_find('.video')[0]['data-autoplay'] == 'False'
    assert world.css_find('.video_control')[0].has_class('play')


@step('creating a video takes a single click')
def video_takes_a_single_click(step):
    assert(not world.is_css_present('.xmodule_VideoModule'))
    world.css_click("a[data-location='i4x://edx/templates/video/default']")
    assert(world.is_css_present('.xmodule_VideoModule'))


@step('I have hidden captions')
def set_show_captions_false(step):
    world.css_click('a.hide-subtitles')


@step('when I view the video it does not show the captions')
def does_not_show_captions(step):
    assert world.css_find('.video')[0].has_class('closed')
