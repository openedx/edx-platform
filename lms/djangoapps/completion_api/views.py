"""
API views to read completion information.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib.auth import get_user_model
from opaque_keys.edx.keys import CourseKey
from progress.models import StudentProgress
from rest_framework.exceptions import NotAuthenticated, NotFound, ParseError, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.lib.api import authentication, paginators

from .models import CourseCompletionFacade, AGGREGATE_CATEGORIES
from .serializers import course_completion_serializer_factory

User = get_user_model()  # pylint: disable=invalid-name


class CompletionViewMixin(object):
    """
    Common functionality for completion views.
    """

    _allowed_requested_fields = AGGREGATE_CATEGORIES

    authentication_classes = (
        authentication.OAuth2AuthenticationAllowInactiveUser,
        authentication.SessionAuthenticationAllowInactiveUser
    )
    permission_classes = (IsAuthenticated,)

    def get_user(self):
        """
        Return the effective user.

        Usually the requesting user, but a staff user can override this.
        """
        requested_username = self.request.GET.get('user')
        if requested_username is None:
            user = self.request.user
        else:
            if self.request.user.is_staff:
                try:
                    user = User.objects.get(username=requested_username)
                except User.DoesNotExist:
                    raise PermissionDenied()
            else:
                if self.request.user.username.lower() == requested_username.lower():
                    user = self.request.user
                else:
                    raise NotFound()
        if not user.is_authenticated():
            raise NotAuthenticated()
        return user

    def get_progress_queryset(self):
        """
        Build a base queryset of relevant StudentProgress objects.
        """
        objs = StudentProgress.objects.filter(user=self.get_user())
        return objs

    def get_requested_fields(self):
        """
        Parse and return value for requested_fields parameter.
        """
        fields = set(field for field in self.request.GET.get('requested_fields', '').split(',') if field)
        diff = fields - self._allowed_requested_fields
        if diff:
            msg = 'Invalid requested_fields value: {}.  Allowed values: {}'
            raise ParseError(msg.format(fields, self._allowed_requested_fields))
        return fields

    def get_serializer(self):
        """
        Return the appropriate serializer.
        """
        return course_completion_serializer_factory(self.get_requested_fields())


class CompletionListView(APIView, CompletionViewMixin):
    """
    API view to render lists of serialized CourseCompletions.

    This is a transitional implementation that uses the
    edx-solutions/progress-edx-platform-extensions models as a backing store.
    """

    pagination_class = paginators.NamespacedPageNumberPagination

    def get(self, request):
        """
        Handler for GET requests.
        """
        self.paginator = self.pagination_class()  # pylint: disable=attribute-defined-outside-init
        paginated = self.paginator.paginate_queryset(self.get_progress_queryset(), self.request, view=self)
        completions = [CourseCompletionFacade(progress) for progress in paginated]
        return self.paginator.get_paginated_response(self.get_serializer()(completions, many=True).data)


class CompletionDetailView(APIView, CompletionViewMixin):
    """
    API view to render serialized CourseCompletions.

    This is a transitional implementation that uses the
    edx-solutions/progress-edx-platform-extensions models as a backing store.
    """

    def get(self, request, course_key):
        """
        Handler for GET requests.
        """
        course_key = CourseKey.from_string(course_key)
        progress = self.get_progress_queryset().get(course_id=course_key)
        completion = CourseCompletionFacade(progress)
        return Response(self.get_serializer()(completion).data)
