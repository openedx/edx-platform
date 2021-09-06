"""
Shareable utilities for third party auth api functions
"""


def filter_user_social_auth_queryset_by_provider(query_set, provider):
    """
    Filter a query set by the given TPA provider

    Params:
        query_set: QuerySet[UserSocialAuth]
        provider: common.djangoapps.third_party_auth.models.ProviderConfig
    Returns:
        QuerySet[UserSocialAuth]
    """
    # Note: When using multi-IdP backend, the provider column isn't
    # enough to identify a specific backend
    filtered_query_set = query_set.filter(provider=provider.backend_name)

    # Test if the current provider has a slug which it appends to
    # uids; these can be used to identify the backend more
    # specifically than the provider's backend
    fake_uid = 'uid'
    uid = provider.get_social_auth_uid(fake_uid)
    if uid != fake_uid:
        # if yes, we add a filter for the slug on uid column
        # carve off the fake_uid from the end, so we get just the prepended slug
        filtered_query_set = filtered_query_set.filter(uid__startswith=uid[:-len(fake_uid)])

    return filtered_query_set
