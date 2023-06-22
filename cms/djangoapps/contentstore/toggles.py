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


# .. toggle_name: new_core_editors.use_video_gallery_flow
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use the video selection gallery on the flow of the new core video xblock editor
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-04-03
# .. toggle_target_removal_date: 2023-6-01
# .. toggle_warning: You need to activate the `new_core_editors.use_new_video_editor` flag to use this new flow.
ENABLE_VIDEO_GALLERY_FLOW_FLAG = WaffleFlag('new_core_editors.use_video_gallery_flow', __name__)


def use_video_gallery_flow():
    """
    Returns a boolean = true if the video gallery flow is enabled
    """
    return ENABLE_VIDEO_GALLERY_FLOW_FLAG.is_enabled()


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


# .. toggle_name: contentstore.enable_studio_content_api
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Enables the new (experimental and unsafe!) Studio Content REST API for course authors,
# .. which provides CRUD capabilities for course content and xblock editing.
# .. Use at your own peril - you can easily delete learner data when editing running courses.
# .. This can be triggered by deleting blocks, editing subsections, problems, assignments, discussions,
# .. creating new problems or graded sections, and by other things you do.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2023-05-26
# .. toggle_tickets: TNL-10208
ENABLE_STUDIO_CONTENT_API = WaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.enable_studio_content_api',
    __name__,
)


def use_studio_content_api():
    """
    Returns a boolean if studio editing API is enabled
    """
    return ENABLE_STUDIO_CONTENT_API.is_enabled()


# .. toggle_name: new_studio_mfe.use_new_home_page
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new studio home page mfe
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-5-15
# .. toggle_target_removal_date: 2023-8-31
# .. toggle_tickets: TNL-9306
# .. toggle_warning:
ENABLE_NEW_STUDIO_HOME_PAGE = WaffleFlag('new_studio_mfe.use_new_home_page', __name__)


def use_new_home_page():
    """
    Returns a boolean if new studio home page mfe is enabled
    """
    return ENABLE_NEW_STUDIO_HOME_PAGE.is_enabled()


# .. toggle_name: new_studio_mfe.use_new_custom_pages
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new studio custom pages mfe
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-5-15
# .. toggle_target_removal_date: 2023-8-31
# .. toggle_tickets: TNL-10619
# .. toggle_warning:
ENABLE_NEW_STUDIO_CUSTOM_PAGES = CourseWaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.new_studio_mfe.use_new_custom_pages', __name__)


def use_new_custom_pages(course_key):
    """
    Returns a boolean if new studio custom pages mfe is enabled
    """
    return ENABLE_NEW_STUDIO_CUSTOM_PAGES.is_enabled(course_key)


# .. toggle_name: new_studio_mfe.use_new_schedule_details_page
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new studio schedule and details mfe
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-5-15
# .. toggle_target_removal_date: 2023-8-31
# .. toggle_tickets: TNL-10619
# .. toggle_warning:
ENABLE_NEW_STUDIO_SCHEDULE_DETAILS_PAGE = CourseWaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.new_studio_mfe.use_new_schedule_details_page', __name__)


def use_new_schedule_details_page(course_key):
    """
    Returns a boolean if new studio schedule and details mfe is enabled
    """
    return ENABLE_NEW_STUDIO_SCHEDULE_DETAILS_PAGE.is_enabled(course_key)


# .. toggle_name: new_studio_mfe.use_new_advanced_settings_page
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new studio advanced settings page mfe
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-5-15
# .. toggle_target_removal_date: 2023-8-31
# .. toggle_tickets: TNL-10619
# .. toggle_warning:
ENABLE_NEW_STUDIO_ADVANCED_SETTINGS_PAGE = CourseWaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.new_studio_mfe.use_new_advanced_settings_page', __name__)


def use_new_advanced_settings_page(course_key):
    """
    Returns a boolean if new studio advanced settings pafe mfe is enabled
    """
    return ENABLE_NEW_STUDIO_ADVANCED_SETTINGS_PAGE.is_enabled(course_key)


# .. toggle_name: new_studio_mfe.use_new_grading_page
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new studio grading page mfe
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-5-15
# .. toggle_target_removal_date: 2023-8-31
# .. toggle_tickets: TNL-10619
# .. toggle_warning:
ENABLE_NEW_STUDIO_GRADING_PAGE = CourseWaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.new_studio_mfe.use_new_grading_page', __name__)


def use_new_grading_page(course_key):
    """
    Returns a boolean if new studio grading mfe is enabled
    """
    return ENABLE_NEW_STUDIO_GRADING_PAGE.is_enabled(course_key)


# .. toggle_name: new_studio_mfe.use_new_updates_page
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new studio updates page mfe
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-5-15
# .. toggle_target_removal_date: 2023-8-31
# .. toggle_tickets: TNL-10619
# .. toggle_warning:
ENABLE_NEW_STUDIO_UPDATES_PAGE = CourseWaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.new_studio_mfe.use_new_updates_page', __name__)


def use_new_updates_page(course_key):
    """
    Returns a boolean if new studio updates mfe is enabled
    """
    return ENABLE_NEW_STUDIO_UPDATES_PAGE.is_enabled(course_key)


# .. toggle_name: new_studio_mfe.use_new_import_page
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new studio import page mfe
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-5-15
# .. toggle_target_removal_date: 2023-8-31
# .. toggle_tickets: TNL-10619
# .. toggle_warning:
ENABLE_NEW_STUDIO_IMPORT_PAGE = CourseWaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.new_studio_mfe.use_new_import_page', __name__)


def use_new_import_page(course_key):
    """
    Returns a boolean if new studio import mfe is enabled
    """
    return ENABLE_NEW_STUDIO_IMPORT_PAGE.is_enabled(course_key)


# .. toggle_name: new_studio_mfe.use_new_export_page
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new studio export page mfe
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-5-15
# .. toggle_target_removal_date: 2023-8-31
# .. toggle_tickets: TNL-10619
# .. toggle_warning:
ENABLE_NEW_STUDIO_EXPORT_PAGE = CourseWaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.new_studio_mfe.use_new_export_page', __name__)


def use_new_export_page(course_key):
    """
    Returns a boolean if new studio export mfe is enabled
    """
    return ENABLE_NEW_STUDIO_EXPORT_PAGE.is_enabled(course_key)


# .. toggle_name: new_studio_mfe.use_new_files_uploads_page
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new studio files and uploads page mfe
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-5-15
# .. toggle_target_removal_date: 2023-8-31
# .. toggle_tickets: TNL-10619
# .. toggle_warning:
ENABLE_NEW_STUDIO_FILES_UPLOADS_PAGE = CourseWaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.new_studio_mfe.use_new_files_uploads_page', __name__)


def use_new_files_uploads_page(course_key):
    """
    Returns a boolean if new studio files and uploads mfe is enabled
    """
    return ENABLE_NEW_STUDIO_FILES_UPLOADS_PAGE.is_enabled(course_key)


# .. toggle_name: new_studio_mfe.use_new_video_uploads_page
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new video uploads page mfe
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-5-15
# .. toggle_target_removal_date: 2023-8-31
# .. toggle_tickets: TNL-10619
# .. toggle_warning:
ENABLE_NEW_STUDIO_VIDEO_UPLOADS_PAGE = CourseWaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.new_studio_mfe.use_new_video_uploads_page', __name__)


def use_new_video_uploads_page(course_key):
    """
    Returns a boolean if new studio video uploads mfe is enabled
    """
    return ENABLE_NEW_STUDIO_VIDEO_UPLOADS_PAGE.is_enabled(course_key)


# .. toggle_name: new_studio_mfe.use_new_course_outline_page
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new studio course outline page mfe
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-5-15
# .. toggle_target_removal_date: 2023-8-31
# .. toggle_tickets: TNL-10619
# .. toggle_warning:
ENABLE_NEW_STUDIO_COURSE_OUTLINE_PAGE = CourseWaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.new_studio_mfe.use_new_course_outline_page', __name__)


def use_new_course_outline_page(course_key):
    """
    Returns a boolean if new studio course outline mfe is enabled
    """
    return ENABLE_NEW_STUDIO_COURSE_OUTLINE_PAGE.is_enabled(course_key)


# .. toggle_name: new_studio_mfe.use_new_unit_page
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new studio course outline page mfe
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-5-15
# .. toggle_target_removal_date: 2023-8-31
# .. toggle_tickets: TNL-10619
# .. toggle_warning:
ENABLE_NEW_STUDIO_UNIT_PAGE = CourseWaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.new_studio_mfe.use_new_unit_page', __name__)


def use_new_unit_page(course_key):
    """
    Returns a boolean if new studio course outline mfe is enabled
    """
    return ENABLE_NEW_STUDIO_UNIT_PAGE.is_enabled(course_key)


# .. toggle_name: new_studio_mfe.use_new_course_team_page
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: This flag enables the use of the new studio course team page mfe
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-5-15
# .. toggle_target_removal_date: 2023-8-31
# .. toggle_tickets: TNL-10619
# .. toggle_warning:
ENABLE_NEW_STUDIO_COURSE_TEAM_PAGE = CourseWaffleFlag(
    f'{CONTENTSTORE_NAMESPACE}.new_studio_mfe.use_new_course_team_page', __name__)


def use_new_course_team_page(course_key):
    """
    Returns a boolean if new studio course team mfe is enabled
    """
    return ENABLE_NEW_STUDIO_COURSE_TEAM_PAGE.is_enabled(course_key)
