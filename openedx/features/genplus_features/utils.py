def get_full_name(user, default=''):
    if user:
        return user.gen_user.name or default
    return default
