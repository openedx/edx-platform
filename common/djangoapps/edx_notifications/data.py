"""
All pure data objects that the various Data Providers will product. This is help avoid
generic dictionaries from being passed around, plus this will help avoid any
implicit database-specific bindings that come with any uses of ORMs.
"""

import copy
from django.core.exceptions import ValidationError

from edx_notifications import const

from edx_notifications.base_data import (
    StringField,
    DictField,
    DateTimeField,
    IntegerField,
    EnumField,
    RelatedObjectField,
    BaseDataObject,
    BooleanField,
)


class NotificationChannel(BaseDataObject):
    """
    Specifies a channel through which a notification is delivered
    """

    # the internal name of the channel
    name = StringField()

    # the human readible name of the channel
    display_name = StringField()

    # the human readible description of the channel
    description_name = StringField()


class NotificationType(BaseDataObject):
    """
    The Data Object representing the NotificationType
    """

    # the name (including namespace) of the notification, e.g. open-edx.lms.forums.reply-to-post
    name = StringField()

    # default delivery channel for this type
    # None = no default
    default_channel = RelatedObjectField(NotificationChannel)

    # renderer class - as a string - that will handle the rendering of
    # this type
    renderer = StringField()

    # any context information to pass into the renderer
    renderer_context = DictField()


class NotificationMessage(BaseDataObject):
    """
    The basic Notification Message
    """

    _exclude_fields_for_equality = ['created', 'modified']  # to account for slight clock skews

    # instance of NotificationMessageType, None = unloaded
    msg_type = RelatedObjectField(NotificationType)

    # namespace is an optional scoping field. This could
    # be used to indicate - for instance - a course_id. Note,
    # that we can filter on this property when
    # getting notifications
    namespace = StringField()

    # unconstained ID to some user identity service (e.g. auth_user in Django)
    from_user_id = IntegerField()

    # dict containing key/value pairs which comprise the notification data payload
    payload = DictField()

    # DateTime, the earliest that this notification should be delivered
    # for example, this could be used for a delayed notification.
    #
    # None = ASAP
    deliver_no_earlier_than = DateTimeField()

    # DateTime, when this notification is no longer considered valid even if it has not been read
    #
    # None = never
    expires_at = DateTimeField()

    # Duration in seconds, when this notification should be purged after being marked as read.
    #
    # None = never
    expires_secs_after_read = IntegerField()

    priority = EnumField(
        allowed_values=[
            const.NOTIFICATION_PRIORITY_NONE,
            const.NOTIFICATION_PRIORITY_LOW,
            const.NOTIFICATION_PRIORITY_MEDIUM,
            const.NOTIFICATION_PRIORITY_HIGH,
            const.NOTIFICATION_PRIORITY_URGENT,
        ],
        default=const.NOTIFICATION_PRIORITY_NONE
    )

    # timestamps
    created = DateTimeField()

    # links to resolve by the NotificationChannel when dispatching.
    resolve_links = DictField()

    # generic id regarding the object that this notification msg is about
    # this can be used for lookups
    object_id = StringField()

    @property
    def _click_link_keyname(self):
        """
        Hide this constant so that other's don't need to know
        how internal schemas
        """
        return '_click_link'

    @property
    def _channel_payloads_keyname(self):
        """
        The name of the dictionary key in the Payload field
        """
        return '__channel_payloads'

    @property
    def _default_payload_keyname(self):
        """
        The name of the dictionary key in the Payload field
        """
        return '__channel_payloads'

    def validate(self):
        """
        Validator for this DataObject

        I'd like to consolidate this to be optional args on the fields and
        have introspection to make sure everything is OK, but since
        Fields are descriptors, that might make things a bit more difficult. Basically
        we need a way to look at the descriptor not the value the descriptor
        reveals
        """

        if not self.msg_type:
            raise ValidationError("Missing required property: msg_type")

    def set_click_link(self, click_link):
        """
        If we have a "click link" associate with the notification,
        this will store it in the system defined meta-field
        in the payload which the Backbone presentation tier
        knows about.

        IMPORTANT: If click links are generated through
        the LinkResolvers in the NotificationChannels
        then it will be overwritten. This happens when
        self.resolve_links != None
        """

        if not self.payload:
            self.payload = {}

        self.payload[self._click_link_keyname] = click_link

    def get_click_link(self):
        """
        Return the click link associated with this message,
        if it was set.

        IMPORTANT: If click links are generated through
        the LinkResolvers in the NotificationChannels
        then it will be overwritten. This happens when
        self.resolve_links != None
        """

        if not self.payload:
            return None

        return self.payload[self._click_link_keyname]

    def add_resolve_link_params(self, link_name, params):
        """
        Helper method to set resolve_links field when the message
        gets published to a channel and we need to add meta-links
        to the message, e.g. to - say - link to a webpage
        """

        if not self.resolve_links:
            self.resolve_links = {}

        if link_name in self.resolve_links:
            # the link_name already exists, so we should update
            # the parameters associated with it
            self.resolve_links[link_name].update(params)
        else:
            # new link name, so let's add the whole thing
            self.resolve_links.update({
                link_name: params
            })

    def add_click_link_params(self, params):
        """
        Helper method to set a system defined '_click_link'
        payload value, which can be handled
        by the front-end Backbone application to
        signify a click through link
        """

        self.add_resolve_link_params(self._click_link_keyname, params)

    def get_click_link_params(self):
        """
        Helper method to get all click links, so that calling
        applications need to know that we store that under
        a key named '_click_link'
        """

        return self.resolve_links.get(self._click_link_keyname)

    @property
    def has_multi_payloads(self):
        """
        Returns true/false if the Message is setup for multi payloads
        """
        return self.payload and self._channel_payloads_keyname in self.payload

    def add_payload(self, payload_dict, channel_name=None):
        """
        Adds a payload that is targeted to the specific channel
        """

        sub_key = self._channel_payloads_keyname
        default_key = self._default_payload_keyname

        # use, old style schema?
        if not channel_name and not self.has_multi_payloads:
            self.payload = payload_dict
        elif channel_name and not self.has_multi_payloads:
            # convert to support multi-payloads
            existing_payload = copy.deepcopy(self.payload)
            self.payload[sub_key] = {}
            payloads = self.payload[sub_key]
            payloads[channel_name] = payload_dict
            payloads[default_key] = existing_payload if existing_payload else {}
        elif channel_name:
            self.payload[sub_key][channel_name] = payload_dict
        else:
            self.payload[sub_key][default_key] = payload_dict

    def get_payload(self, channel_name=None):
        """
        Returns a payload for the specific channel
        """
        if not self.has_multi_payloads:
            return self.payload

        sub_key = self._channel_payloads_keyname
        payloads = self.payload[sub_key]

        if channel_name in payloads:
            return self.payload[sub_key][channel_name]

        default_key = self._default_payload_keyname

        if default_key in payloads:
            return payloads[default_key]

        return {}

    def get_message_for_channel(self, channel_name=None):
        """
        Returns a copy of self with the correct payload channel
        """

        # simple case
        if not self.has_multi_payloads:
            return self

        clone_msg = copy.deepcopy(self)

        # return a NotificationMessage with all other
        # channel payloads removed
        clone_msg.payload = self.get_payload(channel_name)

        return clone_msg


class UserNotification(BaseDataObject):
    """
    Maps a NotificationMessage to a User

    NOTE: We will have to figure out a way to model cursor behavior paging for large
    collections

    NOTE: If we can say that broadcast-type messages, e.g. course-wide, don't need to persist
    read_at state nor any personalization, then we could maybe do away with excessive fan-outs
    """

    # unconstrained pointer to edx-platform auth_user table
    user_id = IntegerField()

    # the message itself
    msg = RelatedObjectField(NotificationMessage)

    # time the user read the notification
    read_at = DateTimeField()

    # dict containing any user specific context (e.g. personalization) for the notification
    user_context = DictField()

    # creation timestamp
    created = DateTimeField()


class NotificationTypeUserChannelPreference(BaseDataObject):
    """
    Specifies a User preference as to how he/she would like notifications of a certain type
    delivered
    """

    # unconstrained identifier that is provided by some identity service (e.g. auth_user Django Auth)
    user_id = IntegerField()

    # the NotificationType this preference is for
    notification_type = RelatedObjectField(NotificationType)

    # the Channel that this NotificationType should route to
    channel = RelatedObjectField(NotificationChannel)

    # dict containing any user specific context for this channel, for example a mobile # for SMS
    # message, or email address
    channel_context = DictField()


class NotificationCallbackTimer(BaseDataObject):
    """
    Registers a callback to occur after a timestamp. This can be used by the
    application tier to evaluate if conditions are met to trigger
    a notification message to be sent.

    A callback can be periodic, in which case, when one callback
    is completed another is schedule as <now>+periodicity_mind. It will reuse the
    same context as when the first was created.

    IMPORTANT: Do not register a lot of high frequency callbacks as
    each reiteration will take up another row in the database to store
    the re-registration of the callback and the results. There is a system limit
    - which is configurable - on the minimum minutes, for example no less than
    60 minutes (hourly job)

    IMPORTANT: the class that is registered to be called back *must*
    implement the NotificationCallbackTimerHandler interface
    """

    @property
    def id(self):
        """
        Alias the timer name as the id, since all data objects have names
        """
        return self.name

    # timer name, must be unique!
    name = StringField()

    # earliest to callback at
    callback_at = DateTimeField()

    # the entry point "e.g. myapp.module.NotificationAsyncCallbackHandler"
    class_name = StringField()

    # is active
    is_active = BooleanField()

    # any specific context that should be passed into the callback
    context = DictField()

    # if this is a recurring timer entry, what is the periodicity
    # in minutes
    periodicity_min = IntegerField()

    # when the callback was called
    executed_at = DateTimeField()

    # any unhandled messages associated with the callback
    err_msg = StringField()

    # any stats the the callback handler returned
    results = DictField()

    # timestamps
    created = DateTimeField()
    modified = DateTimeField()


class NotificationPreference(BaseDataObject):
    """
    Specifies the Notification preference.
    """

    # the internal name of the channel
    name = StringField()

    # display_name for notification preference
    display_name = StringField()

    # display description for notification preference
    display_description = StringField()

    # default_value for notification preference
    default_value = StringField()


class UserNotificationPreferences(BaseDataObject):
    """
    specifies the user notifications preference.
    """

    # unconstrained pointer to edx-platform auth_user table
    user_id = IntegerField()

    # instance of NotificationPreference, None = unloaded
    preference = RelatedObjectField(NotificationPreference)

    value = StringField()

    # timestamps
    created = DateTimeField()
    modified = DateTimeField()
