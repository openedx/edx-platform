"""
...
"""
from openedx.core.lib.block_cache.user_info import UserInfo
from courseware.access import _has_access_to_course


class CourseUserInfo(UserInfo):
    """
    ...
    """
    def __init__(self, course_key, user):
        super(CourseUserInfo, self).__init__()
        self.user = user
        self.course_key = course_key
        self._has_staff_access = None

    @property
    def has_staff_access(self):
        if self._has_staff_access is None:
            self._has_staff_access = _has_access_to_course(self.user, 'staff', self.course_key)
        return self._has_staff_access
