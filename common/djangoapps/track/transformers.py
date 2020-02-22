"""
EventTransformers are data structures that represents events, and modify those
events to match the format desired for the tracking logs.  They are registered
by name (or name prefix) in the EventTransformerRegistry, which is used to
apply them to the appropriate events.
"""


import json
import logging

import six
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey

log = logging.getLogger(__name__)


class DottedPathMapping(object):
    """
    Dictionary-like object for creating keys of dotted paths.

    If a key is created that ends with a dot, it will be treated as a path
    prefix.  Any value whose prefix matches the dotted path can be used
    as a key for that value, but only the most specific match will
    be used.
    """

    # TODO: The current implementation of the prefix registry requires
    # O(number of prefix event transformers) to access an event.  If we get a
    # large number of EventTransformers, it may be worth writing a tree-based
    # map structure where each node is a segment of the match key, which would
    # reduce access time to O(len(match.key.split('.'))), or essentially constant
    # time.

    def __init__(self, registry=None):
        self._match_registry = {}
        self._prefix_registry = {}
        self.update(registry or {})

    def __contains__(self, key):
        try:
            _ = self[key]
            return True
        except KeyError:
            return False

    def __getitem__(self, key):
        if key in self._match_registry:
            return self._match_registry[key]
        if isinstance(key, six.string_types):
            # Reverse-sort the keys to find the longest matching prefix.
            for prefix in sorted(self._prefix_registry, reverse=True):
                if key.startswith(prefix):
                    return self._prefix_registry[prefix]
        raise KeyError('Key {} not found in {}'.format(key, type(self)))

    def __setitem__(self, key, value):
        if key.endswith('.'):
            self._prefix_registry[key] = value
        else:
            self._match_registry[key] = value

    def __delitem__(self, key):
        if key.endswith('.'):
            del self._prefix_registry[key]
        else:
            del self._match_registry[key]

    def get(self, key, default=None):
        """
        Return `self[key]` if it exists, otherwise, return `None` or `default`
        if it is specified.
        """
        try:
            self[key]
        except KeyError:
            return default

    def update(self, dict_):
        """
        Update the mapping with the values in the supplied `dict`.
        """
        for key, value in dict_:
            self[key] = value

    def keys(self):
        """
        Return the keys of the mapping, including both exact matches and
        prefix matches.
        """
        return list(self._match_registry.keys()) + list(self._prefix_registry.keys())


class EventTransformerRegistry(object):
    """
    Registry to track which EventTransformers handle which events.  The
    EventTransformer must define a `match_key` attribute which contains the
    name or prefix of the event names it tracks.  Any `match_key` that ends
    with a `.` will match all events that share its prefix.  A transformer name
    without a trailing dot only processes exact matches.
    """
    mapping = DottedPathMapping()

    @classmethod
    def register(cls, transformer):
        """
        Decorator to register an EventTransformer.  It must have a `match_key`
        class attribute defined.
        """
        cls.mapping[transformer.match_key] = transformer
        return transformer

    @classmethod
    def create_transformer(cls, event):
        """
        Create an EventTransformer of the given event.

        If no transformer is registered to handle the event, this raises a
        KeyError.
        """
        name = event.get(u'name')
        return cls.mapping[name](event)


class EventTransformer(dict):
    """
    Creates a transformer to modify analytics events based on event type.

    To use the transformer, instantiate it using the
    `EventTransformer.create_transformer()` classmethod with the event
    dictionary as the sole argument, and then call `transformer.transform()` on
    the created object to modify the event to the format required for output.

    Custom transformers will want to define some or all of the following values

    Attributes:

        match_key:
            This is the name of the event you want to transform.  If the name
            ends with a `'.'`, it will be treated as a *prefix transformer*.
            All other names denote *exact transformers*.

            A *prefix transformer* will handle any event whose name begins with
            the name of the prefix transformer.  Only the most specific match
            will be used, so if a transformer exists with a name of
            `'edx.ui.lms.'` and another transformer has the name
            `'edx.ui.lms.sequence.'` then an event called
            `'edx.ui.lms.sequence.tab_selected'` will be handled by the
            `'edx.ui.lms.sequence.'` transformer.

            An *exact transformer* will only handle events whose name matches
            name of the transformer exactly.

            Exact transformers always take precedence over prefix transformers.

            Transformers without a name will not be added to the registry, and
            cannot be accessed via the `EventTransformer.create_transformer()`
            classmethod.

        is_legacy_event:
            If an event is a legacy event, it needs to set event_type to the
            legacy name for the event, and may need to set certain event fields
            to maintain backward compatiblity.  If an event needs to provide
            legacy support in some contexts, `is_legacy_event` can be defined
            as a property to add dynamic behavior.

            Default: False

        legacy_event_type:
            If the event is or can be a legacy event, it should define
            the legacy value for the event_type field here.

    Processing methods.  Override these to provide the behavior needed for your
    particular EventTransformer:

        self.process_legacy_fields():
            This method should modify the event payload in any way necessary to
            support legacy event types.  It will only be run if
            `is_legacy_event` returns a True value.

        self.process_event()
            This method modifies the event payload unconditionally.  It will
            always be run.
    """
    def __init__(self, *args, **kwargs):
        super(EventTransformer, self).__init__(*args, **kwargs)
        self.load_payload()

    # Properties to be overridden

    is_legacy_event = False

    @property
    def legacy_event_type(self):
        """
        Override this as an attribute or property to provide the value for
        the event's `event_type`, if it does not match the event's `name`.
        """
        raise NotImplementedError

    # Convenience properties

    @property
    def name(self):
        """
        Returns the event's name.
        """
        return self[u'name']

    @property
    def context(self):
        """
        Returns the event's context dict.
        """
        return self.get(u'context', {})

    # Transform methods

    def load_payload(self):
        """
        Create a data version of self[u'event'] at self.event
        """
        if u'event' in self:
            if isinstance(self[u'event'], six.string_types):
                self.event = json.loads(self[u'event'])
            else:
                self.event = self[u'event']

    def dump_payload(self):
        """
        Write self.event back to self[u'event'].

        Keep the same format we were originally given.
        """
        if isinstance(self.get(u'event'), six.string_types):
            self[u'event'] = json.dumps(self.event)
        else:
            self[u'event'] = self.event

    def transform(self):
        """
        Transform the event with legacy fields and other necessary
        modifications.
        """
        if self.is_legacy_event:
            self._set_legacy_event_type()
            self.process_legacy_fields()
        self.process_event()
        self.dump_payload()

    def _set_legacy_event_type(self):
        """
        Update the event's `event_type` to the value specified by
        `self.legacy_event_type`.
        """
        self['event_type'] = self.legacy_event_type

    def process_legacy_fields(self):
        """
        Override this method to specify how to update event fields to maintain
        compatibility with legacy events.
        """
        pass

    def process_event(self):
        """
        Override this method to make unconditional modifications to event
        fields.
        """
        pass


@EventTransformerRegistry.register
class SequenceTabSelectedEventTransformer(EventTransformer):
    """
    Transformer to maintain backward compatiblity with seq_goto events.
    """

    match_key = u'edx.ui.lms.sequence.tab_selected'
    is_legacy_event = True
    legacy_event_type = u'seq_goto'

    def process_legacy_fields(self):
        self.event[u'old'] = self.event[u'current_tab']
        self.event[u'new'] = self.event[u'target_tab']


class _BaseLinearSequenceEventTransformer(EventTransformer):
    """
    Common functionality for transforming
    `edx.ui.lms.sequence.{next,previous}_selected` events.
    """

    offset = None

    @property
    def is_legacy_event(self):
        """
        Linear sequence events are legacy events if the origin and target lie
        within the same sequence.
        """
        return not self.crosses_boundary()

    def process_legacy_fields(self):
        """
        Set legacy payload fields:
            old: equal to the new current_tab field
            new: the tab to which the user is navigating
        """
        self.event[u'old'] = self.event[u'current_tab']
        self.event[u'new'] = self.event[u'current_tab'] + self.offset

    def crosses_boundary(self):
        """
        Returns true if the navigation takes the focus out of the current
        sequence.
        """
        raise NotImplementedError


@EventTransformerRegistry.register
class NextSelectedEventTransformer(_BaseLinearSequenceEventTransformer):
    """
    Transformer to maintain backward compatiblity with seq_next events.
    """

    match_key = u'edx.ui.lms.sequence.next_selected'
    offset = 1
    legacy_event_type = u'seq_next'

    def crosses_boundary(self):
        """
        Returns true if the navigation moves the focus to the next sequence.
        """
        return self.event[u'current_tab'] == self.event[u'tab_count']


@EventTransformerRegistry.register
class PreviousSelectedEventTransformer(_BaseLinearSequenceEventTransformer):
    """
    Transformer to maintain backward compatiblity with seq_prev events.
    """

    match_key = u'edx.ui.lms.sequence.previous_selected'
    offset = -1
    legacy_event_type = u'seq_prev'

    def crosses_boundary(self):
        """
        Returns true if the navigation moves the focus to the previous
        sequence.
        """
        return self.event[u'current_tab'] == 1


@EventTransformerRegistry.register
class VideoEventTransformer(EventTransformer):
    """
    Converts new format video events into the legacy video event format.

    Mobile devices cannot actually emit events that exactly match their
    counterparts emitted by the LMS javascript video player. Instead of
    attempting to get them to do that, we instead insert a transformer here
    that converts the events they *can* easily emit and converts them into the
    legacy format.
    """
    match_key = u'edx.video.'

    name_to_event_type_map = {
        u'edx.video.played': u'play_video',
        u'edx.video.paused': u'pause_video',
        u'edx.video.stopped': u'stop_video',
        u'edx.video.loaded': u'load_video',
        u'edx.video.position.changed': u'seek_video',
        u'edx.video.seeked': u'seek_video',
        u'edx.video.transcript.shown': u'show_transcript',
        u'edx.video.transcript.hidden': u'hide_transcript',
        u'edx.video.language_menu.shown': u'video_show_cc_menu',
        u'edx.video.language_menu.hidden': u'video_hide_cc_menu',
    }

    is_legacy_event = True

    @property
    def legacy_event_type(self):
        """
        Return the legacy event_type of the current event
        """
        return self.name_to_event_type_map[self.name]

    def transform(self):
        """
        Transform the event with necessary modifications if it is one of the
        expected types of events.
        """
        if self.name in self.name_to_event_type_map:
            super(VideoEventTransformer, self).transform()

    def process_event(self):
        """
        Modify event fields.
        """

        # Convert edx.video.seeked to edx.video.position.changed because edx.video.seeked was not intended to actually
        # ever be emitted.
        if self.name == "edx.video.seeked":
            self['name'] = "edx.video.position.changed"

        if not self.event:
            return

        self.set_id_to_usage_key()
        self.capcase_current_time()

        self.convert_seek_type()
        self.disambiguate_skip_and_seek()
        self.set_page_to_browser_url()
        self.handle_ios_seek_bug()

    def set_id_to_usage_key(self):
        """
        Validate that the module_id is a valid usage key, and set the id field
        accordingly.
        """
        if 'module_id' in self.event:
            module_id = self.event['module_id']
            try:
                usage_key = UsageKey.from_string(module_id)
            except InvalidKeyError:
                log.warning('Unable to parse module_id "%s"', module_id, exc_info=True)
            else:
                self.event['id'] = usage_key.html_id()

            del self.event['module_id']

    def capcase_current_time(self):
        """
        Convert the current_time field to currentTime.
        """
        if 'current_time' in self.event:
            self.event['currentTime'] = self.event.pop('current_time')

    def convert_seek_type(self):
        """
        Converts seek_type to seek and converts skip|slide to
        onSlideSeek|onSkipSeek.
        """
        if 'seek_type' in self.event:
            seek_type = self.event['seek_type']
            if seek_type == 'slide':
                self.event['type'] = "onSlideSeek"
            elif seek_type == 'skip':
                self.event['type'] = "onSkipSeek"
            del self.event['seek_type']

    def disambiguate_skip_and_seek(self):
        """
        For the Android build that isn't distinguishing between skip/seek.
        """
        if 'requested_skip_interval' in self.event:
            if abs(self.event['requested_skip_interval']) != 30:
                if 'type' in self.event:
                    self.event['type'] = 'onSlideSeek'

    def set_page_to_browser_url(self):
        """
        If `open_in_browser_url` is specified, set the page to the base of the
        specified url.
        """
        if 'open_in_browser_url' in self.context:
            self['page'] = self.context.pop('open_in_browser_url').rpartition('/')[0]

    def handle_ios_seek_bug(self):
        """
        Handle seek bug in iOS.

        iOS build 1.0.02 has a bug where it returns a +30 second skip when
        it should be returning -30.
        """
        if self._build_requests_plus_30_for_minus_30():
            if self._user_requested_plus_30_skip():
                self.event[u'requested_skip_interval'] = -30

    def _build_requests_plus_30_for_minus_30(self):
        """
        Returns True if this build contains the seek bug
        """
        if u'application' in self.context:
            if all(key in self.context[u'application'] for key in (u'version', u'name')):
                app_version = self.context[u'application'][u'version']
                app_name = self.context[u'application'][u'name']
                return app_version == u'1.0.02' and app_name == u'edx.mobileapp.iOS'
        return False

    def _user_requested_plus_30_skip(self):
        """
        If the user requested a +30 second skip, return True.
        """

        if u'requested_skip_interval' in self.event and u'type' in self.event:
            interval = self.event[u'requested_skip_interval']
            action = self.event[u'type']
            return interval == 30 and action == u'onSkipSeek'
        else:
            return False
