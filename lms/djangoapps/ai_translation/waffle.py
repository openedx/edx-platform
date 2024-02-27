"""
Waffle config for the AI Translations service
"""

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# Namespace
WAFFLE_NAMESPACE = "ai_translations"
LOG_PREFIX = "AI translations: "

# .. toggle_name: SOME_FEATURE_NAME
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Enabling this feature allows course content to be sent to the AI Translations service
#   for automatic translation of course content.
# .. toggle_warning: Requires ai-translations IDA to be available
# .. toggle_use_cases: opt_in
# .. toggle_creation_date: 2024-02-27
WHOLE_COURSE_TRANSLATIONS = CourseWaffleFlag(
    f"{WAFFLE_NAMESPACE}.whole_course_translations", __name__, LOG_PREFIX
)


def whole_course_translations_enabled_for_course(course_key):
    """Helper to determine if whole course translation is enabled for the given context"""
    return WHOLE_COURSE_TRANSLATIONS.is_enabled(course_key=course_key)
