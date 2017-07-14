"""
Support for per-request messages to be shown to the user.

These utilities are based upon the Django message framework, and allow
code to register messages to be shown to the user on their next page
view. These messages are shown in a page banner which is supported on
all pages that utilize the main.html template.

There are two common use cases:
 - register a message before rendering a view, in which case the message
   will be shown on the resulting page
 - register a message before posting or redirecting. In these situations
   the message will be shown on the subsequent page. This is typically
   used to show a success message to the use.
"""

from enum import Enum

from django.contrib import messages
from openedx.core.djangolib.markup import Text

EDX_USER_MESSAGE_TAG = 'edx-user-message'


class UserMessageType(Enum):
    """
    An enumeration of the types of user messages.
    """
    INFO = messages.constants.INFO
    SUCCESS = messages.constants.SUCCESS
    WARNING = messages.constants.WARNING
    ERROR = messages.constants.ERROR


CSS_CLASSES = {
    UserMessageType.INFO: 'alert-info',
    UserMessageType.SUCCESS: 'alert-success',
    UserMessageType.WARNING: 'alert-warning',
    UserMessageType.ERROR: 'alert-danger',
}

ICON_CLASSES = {
    UserMessageType.INFO: 'fa fa-bullhorn',
    UserMessageType.SUCCESS: 'fa fa-check-circle',
    UserMessageType.WARNING: 'fa fa-warning',
    UserMessageType.ERROR: 'fa fa-warning',
}


class UserMessage():
    """
    Representation of a message to be shown to a user
    """
    def __init__(self, type, message_html):
        assert isinstance(type, UserMessageType)
        self.type = type
        self.message_html = message_html

    @property
    def css_class(self):
        """
        Returns the CSS class to be used on the message element.
        """
        return CSS_CLASSES[self.type]

    @property
    def icon_class(self):
        """
        Returns the CSS icon class representing the message type.
        Returns:
        """
        return ICON_CLASSES[self.type]


def register_user_message(request, message_type, message, title=None):
    """
    Register a message to be shown to the user in the next page.
    """
    assert isinstance(message_type, UserMessageType)
    messages.add_message(request, message_type.value, Text(message), extra_tags=EDX_USER_MESSAGE_TAG)


def register_info_message(request, message, **kwargs):
    """
    Registers an information message to be shown to the user.
    """
    register_user_message(request, UserMessageType.INFO, message, **kwargs)


def register_success_message(request, message, **kwargs):
    """
    Registers a success message to be shown to the user.
    """
    register_user_message(request, UserMessageType.SUCCESS, message, **kwargs)


def register_warning_message(request, message, **kwargs):
    """
    Registers a warning message to be shown to the user.
    """
    register_user_message(request, UserMessageType.WARNING, message, **kwargs)


def register_error_message(request, message, **kwargs):
    """
    Registers an error message to be shown to the user.
    """
    register_user_message(request, UserMessageType.ERROR, message, **kwargs)


def user_messages(request):
    """
    Returns any outstanding user messages.

    Note: this function also marks these messages as being complete
    so they won't be returned in the next request.
    """
    def _get_message_type_for_level(level):
        """
        Returns the user message type associated with a level.
        """
        for __, type in UserMessageType.__members__.items():
            if type.value is level:
                return type
        raise 'Unable to find UserMessageType for level {level}'.format(level=level)

    def _create_user_message(message):
        """
        Creates a user message from a Django message.
        """
        return UserMessage(
            type=_get_message_type_for_level(message.level),
            message_html=unicode(message.message),
        )

    django_messages = messages.get_messages(request)
    return (_create_user_message(message) for message in django_messages if EDX_USER_MESSAGE_TAG in message.tags)
