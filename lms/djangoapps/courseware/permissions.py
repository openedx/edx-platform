"""
Permission definitions for the courseware djangoapp
"""

from bridgekeeper import perms
from .rules import HasAccessRule, HasStaffAccessToContent

MASQUERADE_AS_STUDENT = 'courseware.masquerade_as_student'
VIEW_COURSE_HOME = 'courseware.view_course_home'
VIEW_COURSEWARE = 'courseware.view_courseware'

perms[MASQUERADE_AS_STUDENT] = HasStaffAccessToContent()
perms[VIEW_COURSE_HOME] = HasAccessRule('load')
perms[VIEW_COURSEWARE] = HasAccessRule('load')
