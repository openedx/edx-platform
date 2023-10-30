def get_full_name(instance, default=''):
    name = default
    if instance and instance.profile and (instance.profile.name or '').strip():
        name = instance.profile.name
    elif instance and ((instance.first_name or '').strip() or (instance.last_name or '').strip()):
        name = f'{instance.first_name} {instance.last_name}'.strip()
    return name
