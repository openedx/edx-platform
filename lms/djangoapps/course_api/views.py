"""
Course API Views
"""

import search
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.throttling import UserRateThrottle

from edx_rest_framework_extensions.paginators import NamespacedPageNumberPagination
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes

from . import USE_RATE_LIMIT_2_FOR_COURSE_LIST_API, USE_RATE_LIMIT_10_FOR_COURSE_LIST_API
from .api import course_detail, list_courses
from .forms import CourseDetailGetForm, CourseListGetForm
from .serializers import CourseDetailSerializer, CourseSerializer


@view_auth_classes(is_authenticated=False)
class CourseDetailView(DeveloperErrorViewMixin, RetrieveAPIView):
    """
    **Use Cases**

        Request details for a course

    **Example Requests**

        GET /api/courses/v1/courses/{course_key}/

    **Response Values**

        Body consists of the following fields:

        * effort: A textual description of the weekly hours of effort expected
            in the course.
        * end: Date the course ends, in ISO 8601 notation
        * enrollment_end: Date enrollment ends, in ISO 8601 notation
        * enrollment_start: Date enrollment begins, in ISO 8601 notation
        * id: A unique identifier of the course; a serialized representation
            of the opaque key identifying the course.
        * media: An object that contains named media items.  Included here:
            * course_image: An image to show for the course.  Represented
              as an object with the following fields:
                * uri: The location of the image
        * name: Name of the course
        * number: Catalog number of the course
        * org: Name of the organization that owns the course
        * overview: A possibly verbose HTML textual description of the course.
            Note: this field is only included in the Course Detail view, not
            the Course List view.
        * short_description: A textual description of the course
        * start: Date the course begins, in ISO 8601 notation
        * start_display: Readably formatted start of the course
        * start_type: Hint describing how `start_display` is set. One of:
            * `"string"`: manually set by the course author
            * `"timestamp"`: generated from the `start` timestamp
            * `"empty"`: no start date is specified
        * pacing: Course pacing. Possible values: instructor, self

        Deprecated fields:

        * blocks_url: Used to fetch the course blocks
        * course_id: Course key (use 'id' instead)

    **Parameters:**

        username (optional):
            The username of the specified user for whom the course data
            is being accessed. The username is not only required if the API is
            requested by an Anonymous user.

    **Returns**

        * 200 on success with above fields.
        * 400 if an invalid parameter was sent or the username was not provided
          for an authenticated request.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the course is not available or cannot be seen.

        Example response:

            {
                "blocks_url": "/api/courses/v1/blocks/?course_id=edX%2Fexample%2F2012_Fall",
                "media": {
                    "course_image": {
                        "uri": "/c4x/edX/example/asset/just_a_test.jpg",
                        "name": "Course Image"
                    }
                },
                "description": "An example course.",
                "end": "2015-09-19T18:00:00Z",
                "enrollment_end": "2015-07-15T00:00:00Z",
                "enrollment_start": "2015-06-15T00:00:00Z",
                "course_id": "edX/example/2012_Fall",
                "name": "Example Course",
                "number": "example",
                "org": "edX",
                "overview: "<p>A verbose description of the course.</p>"
                "start": "2015-07-17T12:00:00Z",
                "start_display": "July 17, 2015",
                "start_type": "timestamp",
                "pacing": "instructor"
            }
    """

    serializer_class = CourseDetailSerializer

    def get_object(self):
        """
        Return the requested course object, if the user has appropriate
        permissions.
        """
        requested_params = self.request.query_params.copy()
        requested_params.update({'course_key': self.kwargs['course_key_string']})
        form = CourseDetailGetForm(requested_params, initial={'requesting_user': self.request.user})
        if not form.is_valid():
            raise ValidationError(form.errors)

        return course_detail(
            self.request,
            form.cleaned_data['username'],
            form.cleaned_data['course_key'],
        )


class CourseListUserThrottle(UserRateThrottle):
    """Limit the number of requests users can make to the course list API."""
    # The course list endpoint is likely being inefficient with how it's querying
    # various parts of the code and can take courseware down, it needs to be rate
    # limited until optimized. LEARNER-5527

    THROTTLE_RATES = {
        'user': '20/minute',
        'staff': '40/minute',
    }

    def check_for_switches(self):
        if USE_RATE_LIMIT_2_FOR_COURSE_LIST_API.is_enabled():
            self.THROTTLE_RATES = {
                'user': '2/minute',
                'staff': '10/minute',
            }
        elif USE_RATE_LIMIT_10_FOR_COURSE_LIST_API.is_enabled():
            self.THROTTLE_RATES = {
                'user': '10/minute',
                'staff': '20/minute',
            }

    def allow_request(self, request, view):
        self.check_for_switches()
        # Use a special scope for staff to allow for a separate throttle rate
        user = request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            self.scope = 'staff'
            self.rate = self.get_rate()
            self.num_requests, self.duration = self.parse_rate(self.rate)

        return super(CourseListUserThrottle, self).allow_request(request, view)


@view_auth_classes(is_authenticated=False)
class CourseListView(DeveloperErrorViewMixin, ListAPIView):
    """
    **Use Cases**

        Request information on all courses visible to the specified user.

    **Example Requests**

        GET /api/courses/v1/courses/

    **Response Values**

        Body comprises a list of objects as returned by `CourseDetailView`.

    **Parameters**
        search_term (optional):
            Search term to filter courses (used by ElasticSearch).

        username (optional):
            The username of the specified user whose visible courses we
            want to see. The username is not required only if the API is
            requested by an Anonymous user.

        org (optional):
            If specified, visible `CourseOverview` objects are filtered
            such that only those belonging to the organization with the
            provided org code (e.g., "HarvardX") are returned.
            Case-insensitive.

        mobile (optional):
            If specified, only visible `CourseOverview` objects that are
            designated as mobile_available are returned.

    **Returns**

        * 200 on success, with a list of course discovery objects as returned
          by `CourseDetailView`.
        * 400 if an invalid parameter was sent or the username was not provided
          for an authenticated request.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the specified user does not exist, or the requesting user does
          not have permission to view their courses.

        Example response:

            [
              {
                "blocks_url": "/api/courses/v1/blocks/?course_id=edX%2Fexample%2F2012_Fall",
                "media": {
                  "course_image": {
                    "uri": "/c4x/edX/example/asset/just_a_test.jpg",
                    "name": "Course Image"
                  }
                },
                "description": "An example course.",
                "end": "2015-09-19T18:00:00Z",
                "enrollment_end": "2015-07-15T00:00:00Z",
                "enrollment_start": "2015-06-15T00:00:00Z",
                "course_id": "edX/example/2012_Fall",
                "name": "Example Course",
                "number": "example",
                "org": "edX",
                "start": "2015-07-17T12:00:00Z",
                "start_display": "July 17, 2015",
                "start_type": "timestamp"
              }
            ]
    """

    pagination_class = NamespacedPageNumberPagination
    pagination_class.max_page_size = 100
    serializer_class = CourseSerializer
    throttle_classes = (CourseListUserThrottle,)

    # Return all the results, 10K is the maximum allowed value for ElasticSearch.
    # We should use 0 after upgrading to 1.1+:
    #   - https://github.com/elastic/elasticsearch/commit/8b0a863d427b4ebcbcfb1dcd69c996c52e7ae05e
    results_size_infinity = 10000

    def get_queryset(self):
        """
        Return a list of courses visible to the user.
        """
        form = CourseListGetForm(self.request.query_params, initial={'requesting_user': self.request.user})
        if not form.is_valid():
            raise ValidationError(form.errors)

        db_courses = list_courses(
            self.request,
            form.cleaned_data['username'],
            org=form.cleaned_data['org'],
            filter_=form.cleaned_data['filter_'],
        )

        if not settings.FEATURES['ENABLE_COURSEWARE_SEARCH'] or not form.cleaned_data['search_term']:
            return db_courses

        search_courses = search.api.course_discovery_search(
            form.cleaned_data['search_term'],
            size=self.results_size_infinity,
        )

        search_courses_ids = {course['data']['id']: True for course in search_courses['results']}

        return [
            course for course in db_courses
            if unicode(course.id) in search_courses_ids
        ]
