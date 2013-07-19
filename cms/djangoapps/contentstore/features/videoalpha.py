# disable missing docstring
# pylint: disable=C0111

from lettuce import world, step


@step('when I view the video alpha it does not have autoplay enabled')
def does_not_autoplay(_step):
    assert world.css_find('.videoalpha')[0]['data-autoplay'] == 'False'
    assert world.css_has_class('.video_control', 'play')
