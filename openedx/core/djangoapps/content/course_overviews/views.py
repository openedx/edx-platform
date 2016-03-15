""" Views for courseoverviews."""

from rest_framework.generics import ListAPIView
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.api.view_utils import view_auth_classes

from util.json_request import JsonResponse


@view_auth_classes(is_authenticated=False)
class GetCoursesEnrollmentEndDate(ListAPIView):
    """
    Retrieve course enrollment end date all available courses.

     **Example Requests**

        GET api/courseoverview/enrollment_dates/?exclude_empty=True

    **Querystring**
        exclude_empty: Provide if want to exclude course with empty course enrolment
                    end dates.

    """

    def get(self, request, *args, **kwargs):
        """
        Return a key,value of courses with course_id and enrollments end date
        """
        exclude_empty = request.GET.get('exclude_empty')
        _filter = None

        # Exclude course with empty enrollment_end if `exclude_empty` is given.
        if exclude_empty and exclude_empty.lower() == 'true':
            _filter = dict(enrollment_end__isnull=False)

        courses = CourseOverview.get_all_courses(filter_=_filter)
        courses_enrollment_info = dict(
            (unicode(course_info.id), unicode(course_info.enrollment_end))
            for course_info in courses
        )
        return JsonResponse(data=courses_enrollment_info)
