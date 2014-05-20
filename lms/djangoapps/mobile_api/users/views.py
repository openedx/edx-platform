from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from rest_framework import generics, permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courseware.access import has_access
from student.forms import PasswordResetFormNoActive
from student.models import CourseEnrollment, User
from xmodule.modulestore.django import modulestore

from .serializers import CourseEnrollmentSerializer, UserSerializer


class IsUser(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj


class UserDetail(generics.RetrieveAPIView):
    """Read-only information about our User.

    This will be where users are redirected to after API login and will serve
    as a place to list all useful resources this user can access.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsUser)
    queryset = (
        User.objects.all()
        .select_related('profile', 'course_enrollments')
    )
    serializer_class = UserSerializer
    lookup_field = 'username'


class UserCourseEnrollmentsList(generics.ListAPIView):
    """Read-only list of courses that this user is enrolled in."""
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsUser)
    queryset = CourseEnrollment.objects.all()
    serializer_class = CourseEnrollmentSerializer
    lookup_field = 'username'

    def get_queryset(self):
        qset = self.queryset.filter(
            user__username=self.kwargs['username'], is_active=True
        ).order_by('created')
        return mobile_course_enrollments(qset, self.request.user)

    def get(self, request, *args, **kwargs):
        if request.user.username != kwargs['username']:
            raise PermissionDenied

        return super(UserCourseEnrollmentsList, self).get(self, request, *args, **kwargs)


@api_view(["GET"])
@authentication_classes((OAuth2Authentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def my_user_info(request):
    if not request.user:
        raise PermissionDenied
    return redirect("user-detail", username=request.user.username)

def mobile_course_enrollments(enrollments, user):
    """
    Return enrollments only if courses are mobile_available (or if the user has staff access)
    enrollments is a list of CourseEnrollments.
    """
    for enr in enrollments:
        course = enr.course
        # The course doesn't always really exist -- we can have bad data in the enrollments
        # pointing to non-existent (or removed) courses, in which case `course` is None.
        if course and (course.mobile_available or has_access(user, 'staff', course)):
            yield enr
