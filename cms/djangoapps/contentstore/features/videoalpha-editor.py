# disable missing docstring
# pylint: disable=C0111

from lettuce import world, step


@step('I see the correct videoalpha settings and default values$')
def correct_videoalpha_settings(_step):
    world.verify_all_setting_entries([['Default Speed', '', False],
                                      ['Display Name', 'Video Alpha', False],
                                      ['Download Track', '', False],
                                      ['Download Video', '', False],
                                      ['HTML5 Subtitles', '', False],
                                      ['Show Captions', 'True', False],
                                      ['Speed: .75x', '', False],
                                      ['Speed: 1.25x', '', False],
                                      ['Speed: 1.5x', '', False],
                                      ['Video Sources', '', False]])
