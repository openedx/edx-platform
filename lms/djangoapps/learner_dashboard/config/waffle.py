"""
This module contains various configuration settings via
waffle switches for the learner_dashboard app.
"""

from edx_toggles.toggles import WaffleFlag

# .. toggle_name: learner_dashboard.enable_program_discussions
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable new Program discussion experience for course.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2021-08-25
# .. toggle_target_removal_date: 2021-12-31
# .. toggle_warnings: When the flag is ON, the new experience for Program discussions will be enabled.
# .. toggle_tickets: TNL-8434
ENABLE_PROGRAM_DISCUSSIONS = WaffleFlag(
    'learner_dashboard.enable_program_discussions',
    __name__,
)
