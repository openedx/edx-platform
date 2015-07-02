"""
Discussion API permission logic
"""


def _is_author(cc_content, context):
    """
    Return True if the requester authored the given content, False otherwise
    """
    return context["cc_requester"]["id"] == cc_content["user_id"]


def _is_author_or_privileged(cc_content, context):
    """
    Return True if the requester authored the given content or is a privileged
    user, False otherwise
    """
    return context["is_requester_privileged"] or _is_author(cc_content, context)


def get_editable_fields(cc_content, context):
    """
    Return the set of fields that the requester can edit on the given content
    """
    # Shared fields
    ret = {"abuse_flagged", "voted"}
    if _is_author_or_privileged(cc_content, context):
        ret |= {"raw_body"}

    # Thread fields
    if cc_content["type"] == "thread":
        ret |= {"following"}
        if _is_author_or_privileged(cc_content, context):
            ret |= {"topic_id", "type", "title"}

    # Comment fields
    if (
            cc_content["type"] == "comment" and (
                context["is_requester_privileged"] or (
                    _is_author(context["thread"], context) and
                    context["thread"]["thread_type"] == "question"
                )
            )
    ):
        ret |= {"endorsed"}

    return ret


def can_delete(cc_content, context):
    """
    Return True if the requester can delete the given content, False otherwise
    """
    return _is_author_or_privileged(cc_content, context)
