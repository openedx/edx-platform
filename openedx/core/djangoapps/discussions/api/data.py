import attr


@attr.s(frozen=True)
class ExternalDiscussionData:
    """
    External Discussion Data Object
    """

    context_key = attr.ib(type=str)
    external_discussion_id = attr.ib(type=str)
    usage_key = attr.ib(type=str)
