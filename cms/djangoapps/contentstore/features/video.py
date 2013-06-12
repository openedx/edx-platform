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


@step('I have (hidden|shown) captions')
def hide_or_show_captions(step, shown):
    if shown == 'hidden':
        world.css_click('a.hide-subtitles')


@step('when I view the video it (.*) show the captions')
def does_not_show_captions(step, show_captions):
    # Prevent cookies from overriding course settings
    world.browser.cookies.delete('hide_captions')
    if show_captions == 'does not':
        assert world.css_find('.video')[0].has_class('closed')
    else:
        assert not world.css_find('.video')[0].has_class('closed')


# @step('when I view the video it does show the captions')
# def shows_captions(step):
#     # Prevent cookies from overriding course settings
#     world.browser.cookies.delete('hide_captions')
#     assert not world.css_find('.video')[0].has_class('closed')


@step('I have set "show captions" to (.*)')
def set_show_captions_false(step, setting):
    world.css_click('a.edit-button')
    world.browser.select('Show Captions', setting)
    world.css_click('a.save-button')
