from django.contrib.auth.models import User
from rest_framework.viewsets import ReadOnlyModelViewSet

from notification_prefs import NOTIFICATION_PREF_KEY
from notifier_api.serializers import NotifierUserSerializer
from openedx.core.lib.api.permissions import ApiKeyHeaderPermission


class NotifierUsersViewSet(ReadOnlyModelViewSet):
    """
    An endpoint that the notifier can use to retrieve users who have enabled
    daily forum digests, including all information that the notifier needs about
    such users.
    """
    permission_classes = (ApiKeyHeaderPermission,)
    serializer_class = NotifierUserSerializer
    paginate_by = 10
    paginate_by_param = "page_size"

    # See NotifierUserSerializer for notes about related tables
    queryset = User.objects.filter(
        preferences__key=NOTIFICATION_PREF_KEY
    ).select_related(
        "profile"
    ).prefetch_related(
        "preferences",
        "courseenrollment_set",
        "course_groups",
        "roles__permissions"
    )
