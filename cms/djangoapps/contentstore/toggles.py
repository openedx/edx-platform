"""
CMS feature toggles.
"""
from edx_toggles.toggles import LegacyWaffleFlag, LegacyWaffleFlagNamespace, SettingDictToggle

# .. toggle_name: FEATURES['ENABLE_EXPORT_GIT']
# .. toggle_implementation: SettingDictToggle
# .. toggle_default: False
# .. toggle_description: When enabled, a "Export to Git" menu item is added to the course studio for courses that have a
#   valid "giturl" attribute. Exporting a course to git causes the course to be exported in the directory indicated by
#   the GIT_REPO_EXPORT_DIR setting. Note that when this feature is disabled, courses can still be exported to git with
#   the git_export management command.
# .. toggle_warnings: To enable this feature, the GIT_REPO_EXPORT_DIR setting must be properly defined and point to an
#   existing directory.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2014-02-13
EXPORT_GIT = SettingDictToggle(
    "FEATURES", "ENABLE_EXPORT_GIT", default=False, module_name=__name__
)

# Namespace for studio dashboard waffle flags.
WAFFLE_NAMESPACE = 'contentstore'
WAFFLE_FLAG_NAMESPACE = LegacyWaffleFlagNamespace(name=WAFFLE_NAMESPACE, log_prefix='Contentstore: ')

# .. toggle_name: split_library_on_studio_dashboard
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Enables data new view for library on studio dashboard.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2020-07-8
# .. toggle_tickets: TNL-7536
SPLIT_LIBRARY_ON_DASHBOARD = LegacyWaffleFlag(
    waffle_namespace=LegacyWaffleFlagNamespace(name=WAFFLE_NAMESPACE),
    flag_name='split_library_on_studio_dashboard',
    module_name=__name__
)

# .. toggle_name: course_import_olx_validation
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Enables olx validation during course import.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2021-04-01
# .. toggle_target_removal_date: 2021-05-01
# .. toggle_tickets: TNL-8151
COURSE_IMPORT_OLX_VALIDATION = LegacyWaffleFlag(
    waffle_namespace=LegacyWaffleFlagNamespace(name=WAFFLE_NAMESPACE),
    flag_name='course_import_olx_validation',
    module_name=__name__
)


def split_library_view_on_dashboard():
    """
    check if data new view for library is enabled on studio dashboard.
    """
    return SPLIT_LIBRARY_ON_DASHBOARD.is_enabled()


def course_import_olx_validation_is_enabled():
    """
    Check if course olx validation is enabled on course import.
    """
    return COURSE_IMPORT_OLX_VALIDATION.is_enabled()
