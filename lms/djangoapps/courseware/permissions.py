"""
Permission definitions for the courseware djangoapp
"""

from bridgekeeper import perms
from .rules import HasAccessRule

VIEW_COURSE_HOME = 'courseware.view_course_home'
perms[VIEW_COURSE_HOME] = HasAccessRule('load')
