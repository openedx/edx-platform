# disable missing docstring
#pylint: disable=C0111

from lettuce import world, step


@step('I see the correct settings and default values$')
def i_see_the_correct_settings_and_values(step):
    world.verify_all_setting_entries([['Default Speed', '', False],
                                      ['Display Name', 'default', True],
                                      ['Download Track', '', False],
                                      ['Download Video', '', False],
                                      ['Show Captions', 'True', False],
                                      ['Speed: .75x', '', False],
                                      ['Speed: 1.25x', '', False],
                                      ['Speed: 1.5x', '', False]])
