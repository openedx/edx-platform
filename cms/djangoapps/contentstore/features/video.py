#pylint: disable=C0111

from lettuce import world, step

############### ACTIONS ####################


@step('when I view the video it does not have autoplay enabled')
def does_not_autoplay(step):
    assert world.css_find('.video')[0]['data-autoplay'] == 'False'
    assert world.css_find('.video_control')[0].has_class('play')
