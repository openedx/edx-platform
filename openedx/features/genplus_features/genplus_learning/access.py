from common.djangoapps.student.roles import GlobalStaff
from .roles import ProgramInstructorRole, ProgramStaffRole

ROLES = {
    'instructor': ProgramInstructorRole,
    'staff': ProgramStaffRole,
}


def allow_access(program, level, users):
    change_access(program, level, 'allow', users)


def revoke_access(program, level, users):
    change_access(program, level, 'revoke', users)


def change_access(program, level, action, users):
    try:
        role = ROLES[level](program)
    except KeyError:
        raise ValueError(f"unrecognized level '{level}'")  # lint-amnesty, pylint: disable=raise-missing-from

    if action == 'allow':
        role.add_users(users)
    elif action == 'revoke':
        role.remove_users(users)
    else:
        raise ValueError(f"unrecognized action '{action}'")


def administrative_accesses_to_program_for_user(user, program):
    """
    Returns types of access a user have for given course.
    """
    global_staff = GlobalStaff().has_user(user)
    staff_access = ProgramStaffRole(program).has_user(user)
    instructor_access = ProgramInstructorRole(program).has_user(user)

    return global_staff, staff_access, instructor_access
