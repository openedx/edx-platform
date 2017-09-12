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

    _allowed_requested_fields = AGGREGATE_CATEGORIES | {'mean'}

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
        fields = {
            field for field in self.request.GET.get('requested_fields', '').split(',') if field
        }
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


class CompletionListView(CompletionViewMixin, APIView):
    """
    API view to render serialized CourseCompletions for a single user
    across all enrolled courses.

    **Example Requests**

        GET /api/completion/v0/course/
        GET /api/completion/v0/course/?requested_fields=chapter,vertical

    **Response Values**

        The response is a dictionary comprising pagination data and a page
        of results.

        * pagination: A dict of pagination information, containing the fields:
            * page: The page number of the current set of results.
            * next: The URL for the next page of results, or None if already on
              the last page.
            * previous: The URL for the previous page of results, or None if
              already on the first page.
            * count: The total number of available results.
        * results: A list of dictionaries representing the user's completion
          for each course.

        Standard fields for each completion dictionary:

        * completion: A dictionary comprising of the following fields:
            * earned (float): The sum of the learner's completions.
            * possible (float): The total number of completions available
              in the course.
            * ratio (float in the range [0.0, 1.0]): The ratio of earned
              completions to possible completions in the course.

        Optional fields, as requested in "requested_fields":

        * mean (float): The average completion ratio for all students enrolled
          in the course.
        * Aggregations: The actual fields available are configurable, but
          may include `chapter`, `sequential`, or `vertical`.  If requested,
          the field will be a list of all blocks of that type containing
          completion information for that block.  Fields for each entry will
          include:

              * course_key (CourseKey): The unique course identifier.
              * usage_key: (UsageKey) The unique block identifier.
              * completion: A completion dictionary, identical in format to
                the course-level completion dictionary.

    **Parameters**

        username (optional):
            The username of the specified user for whom the course data is
            being accessed.  If not specified, this defaults to the requesting
            user.

        requested_fields (optional):
            A comma separated list of extra data to be returned.  This can be
            one of the block types specified in `AGGREGATE_CATEGORIES`, or any of
            the other optional fields specified above.  If any invalid fields
            are requested, a 400 error will be returned.

    **Returns**

        * 200 on success with above fields
        * 400 if an invalid value was sent for requested_fields.
        * 403 if a user who does not have permission to masquerade as another
          user specifies a username other than their own.
        * 404 if the course is not available or the requesting user can see no
          completable sections.

        Example response:

            GET /api/course

            {
              "pagination": {
                "count": 14,
                "page": 1,
                "next": "/api/completion/v0/course/?page=2,
                "previous": None
              },
              "results": [
                {
                  "course_key": "edX/DemoX/Demo_course",
                  "completion": {
                    "earned": 42.0,
                    "possible": 54.0,
                    "ratio": 0.77777777777778
                  },
                  "chapter": [
                    {
                      "course_key": "edX/DemoX/Demo_course",
                      "block_key": "i4x://edX/DemoX/chapter/chapter1",
                      "completion": {
                        "earned: 20.0,
                        "possible": 30.0,
                        "ratio": 0.6666666666667
                      }
                    },
                    {
                      "course_key": "edX/DemoX/Demo_course",
                      "block_key": "i4x://edX/DemoX/chapter/chapter2",
                      "completion": {
                        "earned: 22.0,
                        "possible": 24.0,
                        "ratio": 0.9166666666667
                      }
                    }
                  ]
                },
                {
                  "course_key": "course-v1:GeorgetownX+HUMX421-02x+1T2016",
                  "completion": {
                    "earned": 12.0,
                    "possible": 24.0,
                    "ratio": 0.5
                  },
                  "chapter": [
                    {
                      "course_key": "course-v1:GeorgetownX+HUMX421-02x+1T2016",
                      "block_key": "block-v1:GeorgetownX+HUMX421-02x+1T2016+type@chapter+block@Week-2-TheVitaNuova",
                      "completion": {
                        "earned: 12.0,
                        "possible": 24.0,
                        "ratio": 0.5
                      }
                    }
                  ]
                }
              ]
            }

    This is a transitional implementation that uses the
    edx-solutions/progress-edx-platform-extensions models as a backing store.
    The replacement will have the same interface.
    """

    pagination_class = paginators.NamespacedPageNumberPagination

    def get(self, request):
        """
        Handler for GET requests.
        """
        self.paginator = self.pagination_class()  # pylint: disable=attribute-defined-outside-init
        paginated = self.paginator.paginate_queryset(self.get_progress_queryset(), self.request, view=self)
        completions = [CourseCompletionFacade(progress) for progress in paginated]
        serializer = self.get_serializer()(
            instance=completions,
            requested_fields=self.get_requested_fields(),
            many=True
        )
        return self.paginator.get_paginated_response(serializer.data)


class CompletionDetailView(CompletionViewMixin, APIView):
    # pylint: disable=line-too-long
    """
    API view to render a serialized CourseCompletion for a single user in a
    single course.

    **Request Format**

        GET /api/completion/v0/course/<course_key>/

    **Example Requests**

        GET /api/completion/v0/course/course-v1:GeorgetownX+HUMX421-02x+1T2016/
        GET /api/completion/v0/course/course-v1:edX+DemoCourse+Demo2017/?requested_fields=chapter,vertical

    **Response Values**

        Standard fields:

        * course_key (CourseKey): The unique course identifier.
        * completion: A dictionary comprising of the following fields:
            * earned (float): The sum of the learner's completions.
            * possible (float): The total number of completions available
              in the course.
            * ratio (float in the range [0.0, 1.0]): The ratio of earned
              completions to possible completions in the course.

        Optional fields:

        * If "requested_fields" is specified, the response will include data
          for specific block types.  The fields available are configurable, but
          may include `chapter`, `sequential`, or `vertical`.  If requested,
          the block type will be present as another field in the response.
          Inside the field will be a list of all blocks of that type containing
          completion information for that block.  Fields for each entry will
          include:

              * course_key (CourseKey): The unique course identifier.
              * usage_key: (UsageKey) The unique block identifier.
              * completion: A dictionary comprising the following fields.
                  * earned (float): The sum of the learner's completions.
                  * possible (float): The total number of completions
                    available within the identified block.
                  * ratio (float in the range [0.0, 1.0]): The ratio of earned
                    completions to possible completions within the identified
                    block.

    **Parameters**

        username (optional):
            The username of the specified user for whom the course data is
            being accessed.  If not specified, this defaults to the requesting
            user.

        requested_fields (optional):
            A comma separated list of extra data to be returned.  This can be
            one of the block types specified in `AGGREGATE_CATEGORIES`.  If
            specified, completion data is also returned for the requested block
            types.  If any invalid fields are requested, a 400 error will be
            returned.

    **Returns**

        * 200 on success with above fields
        * 400 if an invalid value was sent for requested_fields.
        * 403 if a user who does not have permission to masquerade as another
          user specifies a username other than their own.
        * 404 if the course is not available or the requesting user can see no
          completable sections.

        Example response:

            {
              "course_key": "course-v1:GeorgetownX+HUMX421-02x+1T2016",
              "completion": {
                "earned": 12.0,
                "possible": 24.0,
                "ratio": 0.5
              },
              "mean": 0.25,
              "chapter": [
                {
                  "course_key": "course-v1:GeorgetownX+HUMX421-02x+1T2016",
                  "block_key": "block-v1:GeorgetownX+HUMX421-02x+1T2016+type@chapter+block@Week-2-TheVitaNuova"
                  "completion": {
                    "earned: 12.0,
                    "possible": 24.0,
                    "ratio": 0.5
                  }
                }
              ],
              "sequential": [
                {
                  "course_key": "course-v1:GeorgetownX+HUMX421-02x+1T2016",
                  "block_key": "block-v1:GeorgetownX+HUMX421-02x+1T2016+type@sequential+block@e0eb7cbc1a0c4000bec36b67e622c988",
                  "completion": {
                    "earned: 12.0,
                    "possible": 12.0,
                    "ratio": 1.0
                  }
                },
                {
                  "course_key": "course-v1:GeorgetownX+HUMX421-02x+1T2016",
                  "block_key": "block-v1:GeorgetownX+HUMX421-02x+1T2016+type@sequential+block@f6e7ec3e965b48428197196acf3418e7",
                  "completion": {
                    "earned: 0.0,
                    "possible": 12.0,
                    "ratio": 0.0
                  }
                }
              ]
            }

    This is a transitional implementation that uses the
    edx-solutions/progress-edx-platform-extensions models as a backing store.
    The replacement will have the same interface.
    """
    # pylint: enable=line-too-long

    def get(self, request, course_key):
        """
        Handler for GET requests.
        """
        course_key = CourseKey.from_string(course_key)
        progress = self.get_progress_queryset().get(course_id=course_key)
        completion = CourseCompletionFacade(progress)
        return Response(self.get_serializer()(completion, requested_fields=self.get_requested_fields()).data)
