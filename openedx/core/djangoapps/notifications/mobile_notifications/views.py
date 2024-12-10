from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.notifications.models import (
    CourseNotificationPreference,
    get_course_notification_preference_config_version
)
from openedx.core.djangoapps.notifications.permissions import allow_any_authenticated_user
from .serializers import (
    UserNotificationPreferenceSerializer,
)
from ..config.waffle import ENABLE_NOTIFICATIONS
from ..events import (
    notification_preference_update_event
)
from ..serializers import UserNotificationPreferenceUpdateSerializer


@allow_any_authenticated_user()
class UserNotificationPreferenceView(APIView):
    """
    Supports retrieving and patching the UserNotificationPreference
    model.

    **Example Requests**
        GET /api/notifications/configurations/
        PATCH /api/notifications/configurations/

    **Example Response**:
    [
        {
            'id': 1,
            'course_name': 'testcourse',
            'course_id': 'course-v1:testorg+testcourse+testrun',
            'notification_preference_config': {
                'discussion': {
                    'enabled': False,
                    'core': {
                        'info': '',
                        'web': False,
                        'push': False,
                        'email': False,
                    },
                    'notification_types': {
                        'new_post': {
                            'info': '',
                            'web': False,
                            'push': False,
                            'email': False,
                        },
                    },
                    'not_editable': {},
                },
            }
        },
        {
            'id': 2,
            'course_name': 'testcourse2',
            'course_id': 'course-v1:testorg+testcourse2+testrun',
            'notification_preference_config': {
                'discussion': {
                    'enabled': False,
                    'core': {
                        'info': '',
                        'web': False,
                        'push': False,
                        'email': False,
                    },
                    'notification_types': {
                        'new_post': {
                            'info': '',
                            'web': False,
                            'push': False,
                            'email': False,
                        },
                    },
                    'not_editable': {},
                },
            }
        },

    ]
    """

    def get(self, request, *args, **kwargs):
        """
        Returns notification preferences of all courses user is enrolled in.

         Parameters:
             request (Request): The request object.
         """
        course_ids = self._get_user_active_course_ids(request.user)

        preferences = []
        for course_id in course_ids:
            if ENABLE_NOTIFICATIONS.is_enabled(course_id):
                preference = CourseNotificationPreference.get_updated_user_course_preferences(request.user, course_id)
                preferences.append(preference)

        serializer = UserNotificationPreferenceSerializer(preferences, context={'user': request.user}, many=True)
        return Response(serializer.data)

    def patch(self, request):
        """
        Update all existing user notification preferences with the data in the request body.

        Parameters:
            request (Request): The request object

        Returns:
            200: The updated preference, serialized using the UserNotificationPreferenceSerializer
            404: If the preference does not exist
            403: If the user does not have permission to update the preference
            400: Validation error
        """
        course_ids = self._get_user_active_course_ids(request.user)

        user_course_notification_preferences = list(CourseNotificationPreference.objects.filter(
            user=request.user,
            course_id__in=course_ids,
            is_active=True,
        ))
        updated_notification_preferences = []
        for course_notification_preference in user_course_notification_preferences:
            course_id = course_notification_preference.course_id

            if course_notification_preference.config_version != get_course_notification_preference_config_version():
                error_msg = 'The notification preference config version is not up to date for {}.'.format(course_id)
                return Response({'error': _(error_msg)}, status=status.HTTP_409_CONFLICT, )

            if request.data.get('notification_channel', '') == 'email_cadence':
                request.data['email_cadence'] = request.data['value']
                del request.data['value']

            preference_update = UserNotificationPreferenceUpdateSerializer(
                course_notification_preference, data=request.data, partial=True
            )
            preference_update.is_valid(raise_exception=True)
            updated_notification_preferences.append(preference_update.save())
            notification_preference_update_event(request.user, course_id, preference_update.validated_data)

        serializer_context = {
            'user': request.user
        }
        serializer = UserNotificationPreferenceSerializer(updated_notification_preferences,
                                                          context=serializer_context,
                                                          many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def _get_user_active_course_ids(self, user):
        enrollments = CourseEnrollment.objects.filter(user=user, is_active=True)
        return enrollments.values_list('course_id', flat=True)
