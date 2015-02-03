"""Views served by the embargo app. """

from django.http import Http404
from django.views.generic.base import View
from django.conf import settings

from edxmako.shortcuts import render_to_response

from embargo import messages


class CourseAccessMessageView(View):
    """Show a message explaining that the user was blocked from a course. """

    ENROLLMENT_ACCESS_POINT = 'enrollment'
    COURSEWARE_ACCESS_POINT = 'courseware'

    def get(self, request, access_point=None, message_key=None):
        """Show a message explaining that the user was blocked.

        Arguments:
            request (HttpRequest)

        Keyword Arguments:
            access_point (str): Either 'enrollment' or 'courseware',
                indicating how the user is trying to access the restricted
                content.

            message_key (str): An identifier for which message to show.
                See `embargo.messages` for more information.

        Returns:
            HttpResponse

        Raises:
            Http404: If no message is configured for the specified message key.

        """
        blocked_message = self._message(access_point, message_key)

        if blocked_message is None:
            raise Http404

        return render_to_response(blocked_message.template, {})

    def _message(self, access_point, message_key):
        """Retrieve message information.

        Arguments:
            access_point (str): Either 'enrollment' or 'courseware'
            message_key (str): The identifier for which message to show.

        Returns:
            embargo.messages.BlockedMessage or None

        """
        message_dict = dict()

        # Backwards compatibility with themes created for
        # earlier implementations of the embargo app.
        if settings.FEATURES.get('USE_CUSTOM_THEME') and message_key in messages.CUSTOM_THEME_OVERRIDES:
            message_dict = messages.CUSTOM_THEME_OVERRIDES

        # The access point determines which set of messages to use.
        # This allows us to show different messages to students who
        # are enrolling in a course than we show to students
        # who are enrolled and accessing courseware.
        elif access_point == self.ENROLLMENT_ACCESS_POINT:
            message_dict = messages.ENROLL_MESSAGES
        elif access_point == self.COURSEWARE_ACCESS_POINT:
            message_dict = messages.COURSEWARE_MESSAGES

        return message_dict.get(message_key)
