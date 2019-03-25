"""Util methods for Waffle checks"""

from cms.djangoapps.contentstore.config.waffle import waffle, ENABLE_CHECKLISTS_PAGE, ENABLE_CHECKLISTS_QUALITY
from student.roles import GlobalStaff


def should_show_checklists_page(requesting_user):
    """
        Determine if the ENABLE_CHECKLISTS_PAGE waffle switch is set
        and if the user is able to see it
    """

    if waffle().is_enabled(ENABLE_CHECKLISTS_PAGE):
        if GlobalStaff().has_user(requesting_user):
            return True

    return False


def should_show_checklists_quality(requesting_user, course_key):
    """
        Determine if the ENABLE_CHECKLISTS_QUALITY waffle flag is set
        and if the user is able to see it
    """

    if ENABLE_CHECKLISTS_QUALITY.is_enabled(course_key):
        if GlobalStaff().has_user(requesting_user):
            return True

    return False
