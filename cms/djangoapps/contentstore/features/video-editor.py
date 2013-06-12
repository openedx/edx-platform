# disable missing docstring
#pylint: disable=C0111

from lettuce import world, step


@step('I see the correct settings and default values$')
def i_see_the_correct_settings_and_values(step):
    world.verify_all_setting_entries([['.75x', '', False],
                                      ['1.25x', '', False],
                                      ['1.5x', '', False],
                                      ['Display Name', 'default', True],
                                      ['Normal Speed', '', False],
                                      ['Show Captions', 'True', False],
                                      ['Source', '', False],
                                      ['Track', '', False]])
