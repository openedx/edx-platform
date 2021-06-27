"""
Permission definitions for the contentstore djangoapp
"""

from bridgekeeper import perms

from lms.djangoapps.courseware.rules import HasRolesRule

DELETE_COURSE_CONTENT = 'contentstore.delete_course_content'
perms[DELETE_COURSE_CONTENT] = HasRolesRule('instructor')
