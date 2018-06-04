"""
Miscellaneous waffle switches that both LMS and Studio need to access
"""
from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace

# Namespace
WAFFLE_NAMESPACE = u'course_experience'

# Switches
ENABLE_COURSE_ABOUT_SIDEBAR_HTML = u'enable_about_sidebar_html'


def waffle():
    """
    Returns the namespaced, cached, audited shared Waffle Switch class.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Course Experience: ')
