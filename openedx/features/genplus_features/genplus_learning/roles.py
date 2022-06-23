from xmodule.modulestore.django import modulestore

from common.djangoapps.student.roles import AccessRole
from lms.djangoapps.instructor.access import allow_access, revoke_access
from .models import YearGroup


class YearGroupRole(AccessRole):
    def __init__(self, role_name, year_group: YearGroup):
        super().__init__()
        self.year_group = year_group
        self._role_name = role_name
        self._store = modulestore()

    def has_user(self, gen_user):
        pass

    def add_users(self, *gen_users, send_email):
        units = self.year_group.units.all()
        for unit in units:
            course = self._store.get_course(unit.course_key)
            for gen_user in gen_users:
                allow_access(course, gen_user.user, self._role_name, send_email)

    def remove_users(self, *gen_users, send_email):
        units = self.year_group.units.all()
        for unit in units:
            course = self._store.get_course(unit.course_key)
            for gen_user in gen_users:
                revoke_access(course, gen_user.user, self._role_name, send_email)


    def users_with_role(self):
        pass


class YearGroupStaffRole(YearGroupRole):
    """A Staff member of all courses in a year group"""
    ROLE_NAME = 'staff'

    def __init__(self, *args, **kwargs):
        super().__init__(self.ROLE_NAME, *args, **kwargs)


class YearGroupInstructorRole(YearGroupRole):
    """Instructor of all courses in a year group"""
    ROLE_NAME = 'instructor'

    def __init__(self, *args, **kwargs):
        super().__init__(self.ROLE_NAME, *args, **kwargs)
