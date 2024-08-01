"""
Python APIs exposed by the user_api app to other in-process apps.
"""


from openedx.core.djangoapps.user_api.models import UserRetirementRequest, UserRetirementStatus


def get_retired_user_ids():
    """
    Returns a list of learners' user_ids who have retired their account. This utility method removes any learners who
    are in the "PENDING" retirement state, they have _requested_ retirement but have yet to have all their data purged.
    These learners are still within their cooloff period where they can submit a request to restore their account.

    Args:
        None

    Returns:
        list[int] - A list of user ids of learners who have retired their account, minus any accounts currently in the
            "PENDING" state.
    """
    retired_user_ids = set(UserRetirementRequest.objects.values_list("user_id", flat=True))
    pending_retired_user_ids = set(
        UserRetirementStatus.objects
        .filter(current_state__state_name="PENDING")
        .values_list("user_id", flat=True)
    )

    return list(retired_user_ids - pending_retired_user_ids)
