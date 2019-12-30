"""
Discussion API permission logic
"""


from openedx.core.djangoapps.django_comment_common.comment_client.comment import Comment
from openedx.core.djangoapps.django_comment_common.comment_client.thread import Thread


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


NON_UPDATABLE_THREAD_FIELDS = {"course_id"}
NON_UPDATABLE_COMMENT_FIELDS = {"thread_id", "parent_id"}


def get_initializable_thread_fields(context):
    """
    Return the set of fields that the requester can initialize for a thread

    Any field that is editable by the author should also be initializable.
    """
    ret = get_editable_fields(
        Thread(user_id=context["cc_requester"]["id"], type="thread"),
        context
    )
    ret |= NON_UPDATABLE_THREAD_FIELDS
    return ret


def get_initializable_comment_fields(context):
    """
    Return the set of fields that the requester can initialize for a comment

    Any field that is editable by the author should also be initializable.
    """
    ret = get_editable_fields(
        Comment(user_id=context["cc_requester"]["id"], type="comment"),
        context
    )
    ret |= NON_UPDATABLE_COMMENT_FIELDS
    return ret


def get_editable_fields(cc_content, context):
    """
    Return the set of fields that the requester can edit on the given content
    """

    # For closed thread:
    # no edits, except 'abuse_flagged' and 'read' are allowed for thread
    # no edits, except 'abuse_flagged' is allowed for comment
    ret = {"abuse_flagged"}
    if cc_content["type"] == "thread" and cc_content["closed"]:
        ret |= {"read"}
        return ret
    if cc_content["type"] == "comment" and context["thread"]["closed"]:
        return ret

    # Shared fields
    ret |= {"voted"}
    if _is_author_or_privileged(cc_content, context):
        ret |= {"raw_body"}

    # Thread fields
    if cc_content["type"] == "thread":
        ret |= {"following", "read"}
        if _is_author_or_privileged(cc_content, context):
            ret |= {"topic_id", "type", "title"}
        if context["is_requester_privileged"] and context["discussion_division_enabled"]:
            ret |= {"group_id"}

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
