"""
CMS feature toggles.
"""
from edx_toggles.toggles import SettingDictToggle, WaffleFlag
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# .. toggle_name: FEATURES['ENABLE_EXPORT_GIT']
# .. toggle_implementation: SettingDictToggle
# .. toggle_default: False
# .. toggle_description: When enabled, a "Export to Git" menu item is added to the course studio for courses that have a
#   valid "giturl" attribute. Exporting a course to git causes the course to be exported in the directory indicated by
#   the GIT_REPO_EXPORT_DIR setting. Note that when this feature is disabled, courses can still be exported to git with
#   the git_export management command.
# .. toggle_warning: To enable this feature, the GIT_REPO_EXPORT_DIR setting must be properly defined and point to an
#   existing directory.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2014-02-13
EXPORT_GIT = SettingDictToggle(
    "FEATURES", "ENABLE_EXPORT_GIT", default=False, module_name=__name__
)

# Namespace for studio dashboard waffle flags.
CONTENTSTORE_NAMESPACE = 'contentstore'
CONTENTSTORE_LOG_PREFIX = 'Contentstore: '

# .. toggle_name: contentstore.split_library_on_studio_dashboard
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Enables data new view for library on studio dashboard.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2020-07-8
# .. toggle_tickets: TNL-7536
SPLIT_LIBRARY_ON_DASHBOARD = WaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.split_library_on_studio_dashboard',
    __name__,
    CONTENTSTORE_LOG_PREFIX,
)

# .. toggle_name: contentstore.bypass_olx_failure
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Enables bypassing olx validation failures during course import.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2021-04-15
# .. toggle_target_removal_date: 2021-05-15
# .. toggle_tickets: TNL-8214
BYPASS_OLX_FAILURE = WaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.bypass_olx_failure',
    __name__,
    CONTENTSTORE_LOG_PREFIX,
)


def split_library_view_on_dashboard():
    """
    check if data new view for library is enabled on studio dashboard.
    """
    return SPLIT_LIBRARY_ON_DASHBOARD.is_enabled()


def bypass_olx_failure_enabled():
    """
    Check if bypass is enabled for course olx validation errors.
    """
    return BYPASS_OLX_FAILURE.is_enabled()


# .. toggle_name: FEATURES['ENABLE_EXAM_SETTINGS_HTML_VIEW']
# .. toggle_use_cases: open_edx
# .. toggle_implementation: SettingDictToggle
# .. toggle_default: False
# .. toggle_description: When enabled, users can access the new course authoring view for proctoring exams
# .. toggle_warning: None
# .. toggle_creation_date: 2020-07-23
ENABLE_EXAM_SETTINGS_HTML_VIEW = SettingDictToggle(
    "FEATURES", "ENABLE_EXAM_SETTINGS_HTML_VIEW", default=False, module_name=__name__
)


def exam_setting_view_enabled():
    """
    Returns a boolean if proctoring exam setting mfe view is enabled.
    """
    return ENABLE_EXAM_SETTINGS_HTML_VIEW.is_enabled()


# .. toggle_name: new_core_editors.use_new_text_editor
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new core text xblock editor
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2021-12-1
# .. toggle_target_removal_date: 2022-1-30
# .. toggle_tickets: TNL-9306
# .. toggle_warning:
ENABLE_NEW_TEXT_EDITOR_FLAG = WaffleFlag('new_core_editors.use_new_text_editor', __name__)


def use_new_text_editor():
    """
    Returns a boolean = true if new text editor is enabled
    """
    return ENABLE_NEW_TEXT_EDITOR_FLAG.is_enabled()


# .. toggle_name: new_core_editors.use_new_video_editor
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new core video xblock editor
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2021-12-1
# .. toggle_target_removal_date: 2022-1-30
# .. toggle_tickets: TNL-9306
# .. toggle_warning:
ENABLE_NEW_VIDEO_EDITOR_FLAG = WaffleFlag('new_core_editors.use_new_video_editor', __name__)


def use_new_video_editor():
    """
    Returns a boolean = true if new video editor is enabled
    """
    return ENABLE_NEW_VIDEO_EDITOR_FLAG.is_enabled()


# .. toggle_name: new_core_editors.use_new_problem_editor
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new core problem xblock editor
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2021-12-1
# .. toggle_target_removal_date: 2022-1-30
# .. toggle_tickets: TNL-9306
# .. toggle_warning:
ENABLE_NEW_PROBLEM_EDITOR_FLAG = WaffleFlag('new_core_editors.use_new_problem_editor', __name__)


def use_new_problem_editor():
    """
    Returns a boolean if new problem editor is enabled
    """
    return ENABLE_NEW_PROBLEM_EDITOR_FLAG.is_enabled()


# .. toggle_name: contentstore.individualize_anonymous_user_id
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of unique anonymous_user_id during studio preview
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2022-05-04
# .. toggle_target_removal_date: 2022-05-30
# .. toggle_tickets: MST-1455
INDIVIDUALIZE_ANONYMOUS_USER_ID = CourseWaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.individualize_anonymous_user_id', __name__
)


def individualize_anonymous_user_id(course_id):
    """
    Returns a boolean if individualized anonymous_user_id is enabled on the course
    """
    return INDIVIDUALIZE_ANONYMOUS_USER_ID.is_enabled(course_id)


# .. toggle_name: contentstore.enable_copy_paste_feature
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Moves most component-level actions into a submenu and adds new "Copy Component" and "Paste
#   Component" actions which can be used to copy components (XBlocks) within or among courses.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-02-28
# .. toggle_target_removal_date: 2023-05-01
# .. toggle_tickets: https://github.com/openedx/modular-learning/issues/11 https://github.com/openedx/modular-learning/issues/50
ENABLE_COPY_PASTE_FEATURE = WaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.enable_copy_paste_feature',
    __name__,
    CONTENTSTORE_LOG_PREFIX,
)
