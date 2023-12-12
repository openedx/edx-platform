"""
This module contains various configuration settings via
waffle switches for the Completion app.
"""

from edx_toggles.toggles import WaffleSwitch

# Namespace
WAFFLE_NAMESPACE = 'completion'

# Switches
# TODO: Replace with WaffleSwitch(). See waffle() docstring.
TEACHER_PROGRESS_TACKING_DISABLED_SWITCH = WaffleSwitch(
    f'{WAFFLE_NAMESPACE}.disable_teacher_progress_tracking',
    module_name=__name__
)
