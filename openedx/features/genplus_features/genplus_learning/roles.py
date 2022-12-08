from django.contrib.auth.models import User

from common.djangoapps.student.roles import AccessRole
from .models import Program, ProgramAccessRole
from .cache import ProgramRoleCache


class ProgramRole(AccessRole):
    def __init__(self, role_name, program: Program):
        super().__init__()
        self.program = program
        self._role_name = role_name

    def has_user(self, user, check_user_activation=True):
        if check_user_activation and not user.is_authenticated:
            return False

        if not hasattr(user, '_program_roles'):
            # Cache a list of tuples identifying the particular roles that a user has
            # Stored as tuples, rather than django models, to make it cheaper to construct objects for comparison
            user._program_roles = ProgramRoleCache(user)

        return user._program_roles.has_role(self._role_name, self.program)

    def add_users(self, users):
        for user in users:
            if user.is_authenticated and not self.has_user(user):
                entry = ProgramAccessRole(user=user, role=self._role_name, program=self.program)
                entry.save()
                if hasattr(user, '_program_roles'):
                    del user._program_roles

    def remove_users(self, *users):
        entries = ProgramAccessRole.objects.filter(
            user__in=users, role=self._role_name, program=self.program
        )
        entries.delete()
        for user in users:
            if hasattr(user, '_program_roles'):
                del user._program_roles

    def users_with_role(self):
        entries = User.objects.filter(
            programaccessrole__role=self._role_name,
            programaccessrole__program=self.program
        )
        return entries



class ProgramStaffRole(ProgramRole):
    """A Staff member of all courses in a Program"""
    ROLE_NAME = 'staff'

    def __init__(self, *args, **kwargs):
        super().__init__(self.ROLE_NAME, *args, **kwargs)


class ProgramInstructorRole(ProgramRole):
    """Instructor of all courses in a Program"""
    ROLE_NAME = 'instructor'

    def __init__(self, *args, **kwargs):
        super().__init__(self.ROLE_NAME, *args, **kwargs)
