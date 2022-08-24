"""
Event-tracking additions for Tahoe customer-specific metadata.

Custom event-tracking Processor to add properties to events.
"""


class TahoeUserMetadataProcessor(object):
    """
    Event tracking Processor for Tahoe User Data.

    Always returns the event for continued processing.
    """

    def __call__(self, event):
        """
        TODO: Think whether we really even want a Processor.

        eventtracking.contexts.user_tahoe_idp_metadata_context will
        have added the tahoe user idp metadata ....
        unless the event is not emitted in the context of a request,
        like in the case of edx.bi.completion events emitted as part of a scheduled
        Celery task
        If that's the only important case, we may just want to update
        completion_aggregator.tracking to wrap the event in
        `tracker.get_tracker().enter_context(self.CONTEXT_NAME, context)`
        though we would need to think about how to query site configuration
        """
        return event
