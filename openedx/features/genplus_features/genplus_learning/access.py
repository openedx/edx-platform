from .roles import ProgramInstructorRole, ProgramStaffRole

ROLES = {
    'instructor': ProgramInstructorRole,
    'staff': ProgramStaffRole,
}


def allow_access(program, gen_user, level, send_email=False):
    change_access(program, gen_user, level, 'allow', send_email)


def revoke_access(program, gen_user, level, send_email=False):
    change_access(program, gen_user, level, 'revoke', send_email)


def change_access(program, gen_user, level, action, send_email=False):
    try:
        role = ROLES[level](program)
    except KeyError:
        raise ValueError(f"unrecognized level '{level}'")  # lint-amnesty, pylint: disable=raise-missing-from

    if action == 'allow':
        role.add_users(gen_user, send_email=send_email)
    elif action == 'revoke':
        role.remove_users(gen_user, send_email=send_email)
    else:
        raise ValueError(f"unrecognized action '{action}'")
