"""Util methods for Waffle checks"""


from cms.djangoapps.contentstore.config.waffle import ENABLE_CHECKLISTS_QUALITY


def should_show_checklists_quality(course_key):
    """
        Determine if the ENABLE_CHECKLISTS_QUALITY waffle flag is set
        and if the user is able to see it
    """
    if ENABLE_CHECKLISTS_QUALITY.is_enabled(course_key):
        return True
    return False
