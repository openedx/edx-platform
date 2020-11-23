"""
Miscellaneous waffle switches that both LMS and Studio need to access
"""


from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace

# Namespace
WAFFLE_NAMESPACE = u'course_experience'

# Switches
# .. toggle_name: course_experience.enable_about_sidebar_html
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Used to determine whether to show custom HTML in the sidebar on the internal course about page.
# .. toggle_category: course-experience
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2018-01-26
# .. toggle_expiration_date: ???
# .. toggle_warnings: N/A
# .. toggle_tickets: N/A
# .. toggle_status: supported
ENABLE_COURSE_ABOUT_SIDEBAR_HTML = u'enable_about_sidebar_html'


def waffle():
    """
    Returns the namespaced, cached, audited shared Waffle Switch class.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Course Experience: ')
