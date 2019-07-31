"""
Permission definitions for the courseware djangoapp
"""

from bridgekeeper import perms
from .rules import HasAccessRule, HasStaffAccessToContent

VIEW_COURSE_HOME = 'courseware.view_course_home'
MASQUERADE_AS_STUDENT = 'courseware.masquerade_as_student'

perms[VIEW_COURSE_HOME] = HasAccessRule('load')
perms[MASQUERADE_AS_STUDENT] = HasStaffAccessToContent()
