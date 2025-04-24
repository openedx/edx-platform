"""
Feature toggles used across the platform. Toggles should only be added to this module if we don't have a better place
for them. Generally speaking, they should be added to the most appropriate app or repo.
"""
from edx_toggles.toggles import SettingDictToggle

# .. toggle_name: FEATURES['ENTRANCE_EXAMS']
# .. toggle_implementation: SettingDictToggle
# .. toggle_default: False
# .. toggle_description: Enable entrance exams feature. When enabled, students see an exam xblock as the first unit
#   of the course.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2015-12-01
# .. toggle_tickets: https://openedx.atlassian.net/browse/SOL-40
ENTRANCE_EXAMS = SettingDictToggle(
    "FEATURES", "ENTRANCE_EXAMS", default=False, module_name=__name__
)

# .. toggle_name: entrance_exams
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Enable entrance exams feature. When enabled, students
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2015-12-01
# .. toggle_migration_date: 2025-04-24
# .. toggle_tickets: https://openedx.atlassian.net/browse/SOL-40
# .. toggle_warnings: This replaces the FEATURES['ENTRANCE_EXAMS'] setting
ENTRANCE_EXAMS_FLAG = WaffleFlag('core.entrance_exams', module_name=__name__)


def are_entrance_exams_enabled():
    """
    Returns whether entrance exams are enabled.

    During the transition period, this checks both the old setting and the new
    Once the transition is complete, the old setting check can be removed.
    """
    return ENTRANCE_EXAMS.is_enabled() or ENTRANCE_EXAMS_FLAG.is_enabled()
