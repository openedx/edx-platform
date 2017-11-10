"""
Notification Consumer HTTP-based API enpoints
"""

import logging

from django.http import Http404
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from edx_notifications import const
from edx_notifications.data import NotificationMessage
from edx_notifications.exceptions import (
    ItemNotFoundError,
)
from edx_notifications.lib.consumer import (
    get_notifications_count_for_user,
    get_notifications_for_user,
    get_notification_preferences,
    get_notification_for_user,
    mark_notification_read,
    mark_all_user_notification_as_read,
    get_user_preferences,
    get_user_preference_by_name,
    set_user_notification_preference
)
from edx_notifications.lib.publisher import get_notification_type, \
    bulk_publish_notification_to_users
from edx_notifications.renderers.renderer import (
    get_all_renderers,
)
from student.models import User
from .api_utils import AuthenticatedAPIView

NAMESPACE = 'philu/notifications'

LOG = logging.getLogger("api")

FILTER_PARAMETER_NAMES = [
    ('read', bool),
    ('unread', bool),
    ('namespace', unicode),
    ('msg_type', unicode),
]

OPTIONS_PARAMETER_NAMES = [
    ('offset', int),
    ('limit', int),
]

BOOLEAN_TRUE_STRINGS = [
    'True',
    'true',
    '1',
    'yes',
]

BOOLEAN_FALSE_STRINGS = [
    'False',
    'false',
    '0',
    'no',
]


def _get_parameters_from_request(request, allowed_parameters):
    """
    Helper method to pull parameters from querystring passed in the request URL
    """

    params = {}
    for (filter_name, filter_type) in allowed_parameters:
        if filter_name in request.GET:
            value = None
            str_val = request.GET[filter_name]

            if filter_type == int:
                value = int(str_val)
            elif filter_type == bool:
                if str_val in BOOLEAN_TRUE_STRINGS:
                    value = True
                elif str_val in BOOLEAN_FALSE_STRINGS:
                    value = False
                else:
                    raise ValueError(
                        "Passed in expected bool '{val}' does not map to True or False".format(val=str_val)
                    )
            elif filter_type == str or filter_type == unicode:
                value = str_val
            else:
                raise ValueError('Unknown parameter type {name}'.format(name=filter_type))

            params[filter_name] = value

    return params


def _get_filter_and_options(request):
    """
    Helper method to construct a dict of all filter parameters
    that can be passed in from a query string
    """

    filters = _get_parameters_from_request(request, FILTER_PARAMETER_NAMES)
    options = _get_parameters_from_request(request, OPTIONS_PARAMETER_NAMES)

    return filters, options


class NotificationCount(AuthenticatedAPIView):
    """
    Returns the number of notifications for the logged in user
    """

    def get(self, request):
        """
        HTTP GET Handler
        """

        try:
            filters, __ = _get_filter_and_options(request)
        except ValueError:
            return Response({}, status.HTTP_400_BAD_REQUEST)

        cnt = get_notifications_count_for_user(
            int(request.user.id),
            filters=filters
        )

        return Response(
            {
                'count': cnt,
            },
            status=status.HTTP_200_OK
        )


class NotificationsList(APIView):
    """
    GET returns list of notifications
    """

    def get(self, request):
        """
        HTTP GET Handler
        """

        try:
            filters, options = _get_filter_and_options(request)
        except ValueError:
            return Response({}, status.HTTP_400_BAD_REQUEST)

        user_msgs = get_notifications_for_user(
            int(request.user.id),
            filters=filters,
            options=options,
        )

        resultset = [user_msg.get_fields() for user_msg in user_msgs]

        return Response(resultset, status.HTTP_200_OK)

    def post(self, request):
        """
        HTTP GET Handler
        """
        notification_data = request.POST
        user_ids = []

        for user in notification_data.get('user', []):
            try:
                user = User.objects.get(username=user['username'])
                user_ids.append(user.id)
            except User.DoesNotExist:
                return JsonResponse({'message': "User does not exist for provided username"},
                                    status=status.HTTP_400_BAD_REQUEST)

        type_name = notification_data['notification_type']
        msg_type = get_notification_type(type_name)

        channel_name = request.POST['notification_channel']
        if not channel_name:
            channel_name = None
        msg_type = get_notification_type(type_name)

        msg = NotificationMessage(
            msg_type=msg_type,
            namespace=NAMESPACE,
            payload=self.generate_payload(notification_data),
        )
        bulk_publish_notification_to_users(user_ids, msg, preferred_channel=channel_name)

        return Response([], status.HTTP_200_OK)

    def generate_payload(self, notification_data):
        payload = dict(notification_data)
        payload.pop('user', None)


def _find_notification_by_id(user_id, msg_id):
    """
    Helper method to look up a notification for a user, if it is not
    found then raise a Http404
    """

    try:
        user_msg = get_notification_for_user(int(user_id), int(msg_id))
    except ItemNotFoundError:
        raise Http404()

    return user_msg


class NotificationDetail(AuthenticatedAPIView):
    """
    GET returns details on the notifications
    POST can mark notification
    """

    _allowed_post_parameters = {
        'mark_as': ['read', 'unread'],
    }

    def get(self, request, msg_id):
        """
        HTTP GET Handler
        """

        # Get msg for user, raise Http404 if not found
        user_msg = _find_notification_by_id(int(request.user.id), int(msg_id))

        return Response(user_msg.get_fields(), status.HTTP_200_OK)

    def post(self, request, msg_id):
        """
        HTTP POST Handler which is used for such use-cases as 'mark as read'
        and 'mark as unread'
        """

        # make sure we only have expected parameter names and values
        if not self.validate_post_parameters(request):
            return Response({}, status.HTTP_400_BAD_REQUEST)

        if 'mark_as' in request.data:
            mark_as_read = request.data['mark_as'] == 'read'
            try:
                # this will raise an ItemNotFoundError if the user_id/msg_id combo
                # cannot be found
                mark_notification_read(int(request.user.id), int(msg_id), read=mark_as_read)
            except ItemNotFoundError:
                raise Http404()

        return Response([], status.HTTP_200_OK)


class MarkNotificationsAsRead(AuthenticatedAPIView):
    """
    Mark all the user notifications as read
    """

    def post(self, request):
        """
        HTTP POST Handler which is used for such use-cases as 'mark as read'
        """

        filters = None

        # get the namespace from the POST parameters
        if 'namespace' in request.POST:
            filters = {
                'namespace': request.POST['namespace']
            }

        mark_all_user_notification_as_read(
            int(request.user.id),
            filters=filters
        )

        return Response([], status.HTTP_200_OK)


class NotificationPreferenceList(AuthenticatedAPIView):
    """
    GET returns a list of all possible notification preferences that the user could set.
    """

    def get(self, request):  # pylint: disable=unused-argument
        """
        HTTP Get Handler
        """
        notification_preferences = get_notification_preferences()
        result_set = [notification_preference.get_fields() for notification_preference in notification_preferences]

        return Response(result_set, status.HTTP_200_OK)


class UserPreferenceList(AuthenticatedAPIView):
    """
    Returns all preference setting for the request.user
    """

    def get(self, request):
        """
        HTTP Get Handler
        """
        user_preferences = get_user_preferences(int(request.user.id))
        result_set = [user_preference.get_fields() for user_preference in user_preferences]

        return Response(result_set, status.HTTP_200_OK)


class UserPreferenceDetail(AuthenticatedAPIView):
    """
    GET returns the specific preference setting for the authenticated request.user
    POST sets the preference for the authenticated request.user
    """

    def get(self, request, name):
        """
        HTTP Get Handler
        """
        try:
            # this will raise an ItemNotFoundError if the user_id/name combo
            # cannot be found
            user_preference = get_user_preference_by_name(int(request.user.id), name)
        except ItemNotFoundError:
            raise Http404()

        return Response([user_preference.get_fields()], status.HTTP_200_OK)

    def post(self, request, name):
        """
        HTTP POST Handler
        """
        if 'value' not in request.data:
            raise Http404()

        try:
            # this will raise an ItemNotFoundError
            # if the notification_preference cannot be found
            value = request.data.get('value')
            set_user_notification_preference(int(request.user.id), name, value)

            if const.NOTIFICATION_ENFORCE_SINGLE_DIGEST_PREFERENCE:
                # If the user sets one digest preference, make sure
                # only one of them is enabled, i.e. turn off the other one
                is_digest_setting = (
                    name in [
                        const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME,
                        const.NOTIFICATION_WEEKLY_DIGEST_PREFERENCE_NAME
                    ]
                )

                if is_digest_setting and value.lower() == 'true':
                    other_setting = const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME if name \
                                                                                       == const.NOTIFICATION_WEEKLY_DIGEST_PREFERENCE_NAME else \
                        const.NOTIFICATION_WEEKLY_DIGEST_PREFERENCE_NAME

                    # turn off the other setting
                    set_user_notification_preference(int(request.user.id), other_setting, "false")

        except ItemNotFoundError:
            raise Http404()

        return Response([], status.HTTP_200_OK)


class RendererTemplatesList(AuthenticatedAPIView):
    """
    GET returns a list of all Underscore templates that have been registered in the system
    """

    def get(self, request):  # pylint: disable=unused-argument
        """
        HTTP Get Handler
        """

        result_dict = {}

        for class_name, renderer in get_all_renderers().iteritems():
            if renderer.can_render_format(const.RENDER_FORMAT_HTML):
                result_dict[class_name] = renderer.get_template_path(const.RENDER_FORMAT_HTML)

        return Response(result_dict, status.HTTP_200_OK)
