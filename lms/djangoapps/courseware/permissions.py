"""
Permission definitions for the courseware djangoapp
"""

from bridgekeeper import perms
from lms.djangoapps.courseware.rules import HasAccessRule

ACCESS_COURSE = 'courseware.access_course'
EDIT_BOOKMARK = 'courseware.edit_bookmark'
VIEW_COURSE_HOME = 'courseware.view_course_home'
VIEW_COURSEWARE = 'courseware.view_courseware'
VIEW_XQA_INTERFACE = 'courseware.view_xqa_interface'

perms[ACCESS_COURSE] = HasAccessRule('staff')
perms[EDIT_BOOKMARK] = HasAccessRule('staff')
perms[VIEW_COURSE_HOME] = HasAccessRule('load')
perms[VIEW_COURSEWARE] = HasAccessRule('load')
perms[VIEW_XQA_INTERFACE] = HasAccessRule('staff')
