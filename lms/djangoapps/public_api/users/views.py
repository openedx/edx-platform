from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.conf import settings

from rest_framework import generics, permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from student.forms import PasswordResetFormNoActive
from student.models import CourseEnrollment, User

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
        qset = self.queryset.filter(user__username=self.kwargs['username'], is_active=True).order_by('created')
        # return the courses that are enabled for mobile
        return (ce for ce in qset if ce.course.mobile_available)

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

@api_view(["POST"])
def password_reset(request):
    form = PasswordResetFormNoActive({"email": request.DATA.get("email")})
    if form.is_valid():
        form.save(use_https=request.is_secure(),
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  request=request,
                  domain_override=request.get_host())
        return Response({}, status=200)
    return Response(form.errors, status=400)
