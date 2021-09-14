import beeline

from social_core.pipeline.user import create_user


@beeline.traced('tahoe_social_auth.create_user_with_logs')
def create_user_with_logs(*args, **kwargs):
    """
    A proxy for social_core.pipeline.user.create_user with beeline monitoring.

    :param args: whatever comes from the social auth pipeline.
    :param kwargs: whatever comes from the social auth pipeline.
    :return: result dict for social auth pipeline.
    """
    beeline.add_context_field('create_user__user_param', kwargs.get('user'))
    result = create_user(*args, **kwargs)
    user = result.get('user')

    beeline.add_context_field('create_user_result', result)
    beeline.add_context_field('is_new_user', result.get('is_new'))
    beeline.add_context_field('create_user__username', getattr(user, 'username', None))
    try:
        beeline.add_context_field('create_user__is_active', user.is_active)
    except AttributeError:
        beeline.add_context_field('create_user__is_active', 'N/A')
    return result
