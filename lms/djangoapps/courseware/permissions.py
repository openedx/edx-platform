"""
Permission definitions for the courseware djangoapp
"""

from bridgekeeper import perms
from .rules import HasAccessRule

perms['courseware.view_course_home'] = HasAccessRule('load')
perms['dashboard.view_courseware_links'] = HasAccessRule('load')
