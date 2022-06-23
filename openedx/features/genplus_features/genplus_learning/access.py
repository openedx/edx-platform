from .roles import YearGroupInstructorRole, YearGroupStaffRole

ROLES = {
    'instructor': YearGroupInstructorRole,
    'staff': YearGroupStaffRole,
}


def allow_access(year_group, gen_user, level, send_email=False):
    _change_access(year_group, gen_user, level, 'allow', send_email)


def revoke_access(year_group, gen_user, level, send_email=False):
    _change_access(year_group, gen_user, level, 'revoke', send_email)


def _change_access(year_group, gen_user, level, action, send_email):
    try:
        role = ROLES[level](year_group)
    except KeyError:
        raise ValueError(f"unrecognized level '{level}'")  # lint-amnesty, pylint: disable=raise-missing-from

    if action == 'allow':
        role.add_users(gen_user, send_email=send_email)
    elif action == 'revoke':
        role.remove_users(gen_user, send_email=send_email)
    else:
        raise ValueError(f"unrecognized action '{action}'")
