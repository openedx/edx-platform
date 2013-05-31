#pylint: disable=C0111

from lettuce import world, step
from common import *

############### ACTIONS ####################


@step('when I view it it does not autoplay')
def does_not_autoplay(step):
    assert world.css_find('.video')[0]['data-autoplay'] == 'False'
    assert world.css_find('.video_control')[0].has_class('play')
