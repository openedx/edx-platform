"""
Miscellaneous waffle switches that both LMS and Studio need to access
"""


from edx_toggles.toggles import WaffleSwitchNamespace

# Namespace
WAFFLE_NAMESPACE = u'course_experience'

# Switches
# .. toggle_name: course_experience.enable_about_sidebar_html
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Used to determine whether to show custom HTML in the sidebar on the internal course about page.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2018-01-26
# .. toggle_target_removal_date: None
# .. toggle_warnings: None
# .. toggle_tickets: None
ENABLE_COURSE_ABOUT_SIDEBAR_HTML = u'enable_about_sidebar_html'


def waffle():
    """
    Returns the namespaced, cached, audited shared Waffle Switch class.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Course Experience: ')
