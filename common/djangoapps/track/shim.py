"""Map new event context values to old top-level field values. Ensures events can be parsed by legacy parsers."""

CONTEXT_FIELDS_TO_INCLUDE = [
    'username',
    'session',
    'ip',
    'agent',
    'host'
]


class LegacyFieldMappingProcessor(object):
    """Ensures all required fields are included in emitted events"""

    def __call__(self, event):
        if 'context' in event:
            context = event['context']
            for field in CONTEXT_FIELDS_TO_INCLUDE:
                if field in context:
                    event[field] = context[field]
                else:
                    event[field] = ''
            remove_shim_context(event)

        if 'event_type' in event.get('context', {}):
            event['event_type'] = event['context']['event_type']
            del event['context']['event_type']
        else:
            event['event_type'] = event.get('name', '')

        if 'data' in event:
            event['event'] = event['data']
            del event['data']
        else:
            event['event'] = {}

        if 'timestamp' in event:
            event['time'] = event['timestamp']
            del event['timestamp']

        event['event_source'] = 'server'
        event['page'] = None


def remove_shim_context(event):
    if 'context' in event:
        context = event['context']
        # These fields are present elsewhere in the event at this point
        context_fields_to_remove = set(CONTEXT_FIELDS_TO_INCLUDE)
        # This field is only used for Segment.io web analytics and does not concern researchers
        context_fields_to_remove.add('client_id')
        for field in context_fields_to_remove:
            if field in context:
                del context[field]
