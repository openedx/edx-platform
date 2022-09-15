"""Tahoe version 1 API views

Only include view classes here. See the tests/test_permissions.py:get_api_classes()
method.
"""
from functools import partial
import beeline
import logging
import random
import string

from django.contrib.auth import get_user_model
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
import django.contrib.sites.shortcuts


from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response

from lms.djangoapps.courseware.courses import get_course_by_id

from openedx.core.djangoapps.enrollments.serializers import CourseEnrollmentSerializer
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_authn.views.register import create_account_with_params
from openedx.core.djangoapps.user_authn.views.password_reset import PasswordResetFormNoActive
from student.helpers import AccountValidationError

from student.models import CourseEnrollment

from .mixins import TahoeAuthMixin

from lms.djangoapps.instructor.enrollment import (
    enroll_email,
    get_email_params,
    unenroll_email,
)

from openedx.core.djangoapps.appsembler.api.helpers import as_course_key, normalize_bool_param
from openedx.core.djangoapps.appsembler.api.v1.api import (
    account_exists,
    enroll_learners_in_course,
    unenroll_learners_in_course,
)
from openedx.core.djangoapps.appsembler.api.v1.filters import (
    CourseEnrollmentFilter,
    CourseOverviewFilter,
    UserIndexFilter,
)
from openedx.core.djangoapps.appsembler.api.v1.pagination import (
    TahoeLimitOffsetPagination
)
from openedx.core.djangoapps.appsembler.api.v1.serializers import (
    CourseOverviewSerializer,
    BulkEnrollmentSerializer,
    UserIndexSerializer,
)
from openedx.core.djangoapps.appsembler.tahoe_idp import helpers as tahoe_idp_helpers

# TODO: Just move into v1 directory
from openedx.core.djangoapps.appsembler.api.permissions import (
    TahoeAPIUserThrottle
)
from openedx.core.djangoapps.appsembler.api.sites import (
    get_courses_for_site,
    get_site_for_course,
    get_enrollments_for_site,
    course_belongs_to_site,
    get_users_for_site,
)


log = logging.getLogger(__name__)

#
# Helper functions
#


def create_password():
    """
    Copied from appsembler_api `CreateUserAccountWithoutPasswordView`
    """
    return ''.join(
        random.choice(
            string.ascii_uppercase + string.ascii_lowercase + string.digits)
        for _ in range(32))


@beeline.traced(name="apis.v1.views.send_password_reset_email")
def send_password_reset_email(request):
    """Copied/modified from appsembler_api.utils in enterprise Ginkgo
    Copied the template files from enterprise Ginkgo LMS templates
    """
    form = PasswordResetFormNoActive(request.data)
    if form.is_valid():
        form.save(
            use_https=request.is_secure(),
            from_email=configuration_helpers.get_value(
                'email_from_address', settings.DEFAULT_FROM_EMAIL),
            request=request,
            domain_override=request.get_host(),
            subject_template_name='appsembler/emails/set_password_subject.txt',
            email_template_name='appsembler/emails/set_password_email.html')
        return True
    else:
        return False


class RegistrationViewSet(TahoeAuthMixin, viewsets.ViewSet):
    """
    Allows remote clients to register new users via API

    This API has a rate limit of 60 requets per minutes
    """
    throttle_classes = (TahoeAPIUserThrottle,)
    http_method_names = ['post', 'head']

    @method_decorator(transaction.non_atomic_requests)
    def dispatch(self, *args, **kwargs):
        return super(RegistrationViewSet, self).dispatch(*args, **kwargs)

    @beeline.traced(name="apis.v1.views.RegistrationViewSet.create")
    def create(self, request):
        """Creates a new user account for the site that calls this view

        To use, perform a token authenticated POST to the URL::

            /tahoe/api/v1/registrations/

        Required arguments (JSON data):
            "username"
            "email"
            "name"

        Optional arguments:
            "password"
            "send_activation_email"

        Returns:
            HttpResponse: 200 on success, {"user_id ": 9}
            HttpResponse: 400 if the request is not valid.
            HttpResponse: 409 if an account with the given username or email
                address already exists

        The code here is adapted from the LMS ``appsembler_api`` bulk registration
        code. See the ``appsembler/ginkgo/master`` branch
        """
        if tahoe_idp_helpers.is_tahoe_idp_enabled():
            return Response(
                dict(user_message='This API is not available for this site. Please use the Identity Provider API.'),
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        # Using .copy() to make the POST data mutable
        # see: https://stackoverflow.com/a/49794425/161278
        data = request.data.copy()
        password_provided = 'password' in data

        # set the honor_code and honor_code like checked,
        # so we can use the already defined methods for creating an user
        data['honor_code'] = 'True'
        data['terms_of_service'] = 'True'

        if password_provided:
            try:
                # Default behavior is True - send the email
                data['send_activation_email'] = normalize_bool_param(data.get('send_activation_email', True))
            except ValueError:
                errors = {
                    'user_message': '{0} is not a valid value for "send_activation_email"'.format(
                        data['send_activation_email'])
                }
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            data['password'] = create_password()
            data['send_activation_email'] = False

        email = request.data.get('email')
        username = request.data.get('username')

        # Handle duplicate email/username
        if account_exists(email=email, username=username):
            errors = {"user_message": "User already exists"}
            return Response(errors, status=status.HTTP_409_CONFLICT)

        try:
            user = create_account_with_params(
                request=request,
                params=data,
            )
            if password_provided:
                # if send_activation_email is True, we want to keep the user
                # inactive until the email is properly validated. If the param
                # is False, we activate it.
                user.is_active = not data['send_activation_email']
            else:
                # if the password is not provided, keep the user inactive until
                # the password is set.
                user.is_active = False
            user.save()
            user_id = user.id
            if not password_provided:
                success = send_password_reset_email(request)
                if not success:
                    log.error('Tahoe Reg API: Error sending password reset '
                              'email to user {}'.format(user.username))

        except ValidationError as err:
            log.error('ValidationError. err={}'.format(err))
            # Should only get non-field errors from this function

            assert NON_FIELD_ERRORS not in err.message_dict
            # Only return first error for each field
            # TODO: Let's give a clue as to which are the error causing fields
            msg = 'Invalid parameters on user creation'
            return Response(dict(user_message=msg), status=status.HTTP_400_BAD_REQUEST)
        except AccountValidationError as err:
            log.error('AccountValidationError. err={}'.format(err))
            # Should only get non-field errors from this function

            # assert NON_FIELD_ERRORS not in err.message_dict
            # Only return first error for each field
            # TODO: Let's give a clue as to which are the error causing fields
            msg = 'Invalid parameters on user creation: {field}'.format(
                field=err.field)
            return Response(dict(user_message=msg), status=status.HTTP_400_BAD_REQUEST)
        return Response({'user_id ': user_id}, status=status.HTTP_200_OK)


class CourseViewSet(TahoeAuthMixin, viewsets.ReadOnlyModelViewSet):
    """Provides course information

    To provide data for all courses on your site::

        GET /tahoe/api/v1/courses/

    To provide details on a specific course::

        GET /tahoe/api/v1/courses/<course id>/

    """
    model = CourseOverview
    pagination_class = TahoeLimitOffsetPagination
    serializer_class = CourseOverviewSerializer
    throttle_classes = (TahoeAPIUserThrottle,)
    filter_backends = (DjangoFilterBackend, )
    filterset_class = CourseOverviewFilter

    @beeline.traced(name="apis.v1.views.CourseViewSet.get_queryset")
    def get_queryset(self):
        site = django.contrib.sites.shortcuts.get_current_site(self.request)
        queryset = get_courses_for_site(site)
        return queryset

    @beeline.traced(name="apis.v1.views.CourseViewSet.retrieve")
    def retrieve(self, request, *args, **kwargs):
        course_id_str = kwargs.get('pk', '')
        course_key = as_course_key(course_id_str.replace(' ', '+'))
        site = django.contrib.sites.shortcuts.get_current_site(request)
        if site != get_site_for_course(course_key):
            # Raising NotFound instead of PermissionDenied
            raise NotFound()
        course_overview = get_object_or_404(CourseOverview, pk=course_key)
        return Response(CourseOverviewSerializer(course_overview).data)


# @can_disable_rate_limit
class EnrollmentViewSet(TahoeAuthMixin, viewsets.ModelViewSet):
    """Provides course information

    To provide data for all enrollments on your site::

        GET /tahoe/api/v1/enrollments/

    To provide enrollments for a specific course::

        GET /tahoe/api/v1/enrollments/<course id>/

    """
    model = CourseEnrollment
    pagination_class = TahoeLimitOffsetPagination
    serializer_class = CourseEnrollmentSerializer
    throttle_classes = (TahoeAPIUserThrottle,)
    filter_backends = (DjangoFilterBackend, )
    filterset_class = CourseEnrollmentFilter

    @beeline.traced(name="apis.v1.views.EnrollmentViewSet.get_queryset")
    def get_queryset(self):
        site = django.contrib.sites.shortcuts.get_current_site(self.request)
        queryset = get_enrollments_for_site(site)
        return queryset

    @beeline.traced(name="apis.v1.views.EnrollmentViewSet.retrieve")
    def retrieve(self, request, *args, **kwargs):
        course_id_str = kwargs.get('pk', '')
        course_key = as_course_key(course_id_str.replace(' ', '+'))
        site = django.contrib.sites.shortcuts.get_current_site(request)
        if site != get_site_for_course(course_key):
            # Raising NotFound instead of PermissionDenied
            raise NotFound()
        course_overview = get_object_or_404(CourseOverview, pk=course_key)
        return Response(CourseOverviewSerializer(course_overview).data)

    @beeline.traced(name="apis.v1.views.EnrollmentViewSet.create")
    def create(self, request, *args, **kwargs):
        """
        Adapts interface from bulk enrollment

        """
        site = django.contrib.sites.shortcuts.get_current_site(request)
        serializer = BulkEnrollmentSerializer(data=request.data)
        if serializer.is_valid():
            # TODO: Follow-on: Wrap in transaction
            # TODO: trap error on each attempt and log
            # IMPORTANT: THIS IS A WIP to get this working quickly
            # Being clean inside is secondary

            invalid_course_ids = [course_id for course_id in serializer.data.get('courses')
                                  if not course_belongs_to_site(site, course_id)]

            if invalid_course_ids:
                # Don't do bulk enrollment. Return error message and failing
                # course ids
                response_data = {
                    'error': 'invalid-course-ids',
                    'invalid_course_ids': invalid_course_ids,
                }
                response_code = status.HTTP_400_BAD_REQUEST
            else:
                action = serializer.data.get('action')
                if action in {'enroll', 'unenroll'}:
                    # Do bulk enrollment
                    email_learners = serializer.data.get('email_learners')
                    identifiers = serializer.data.get('identifiers')
                    auto_enroll = serializer.data.get('auto_enroll')
                    response_code = status.HTTP_201_CREATED if action == 'enroll' else status.HTTP_200_OK
                    results = []

                    for course_id in serializer.data.get('courses'):
                        course_key = as_course_key(course_id)
                        # TODO: The two checks below deserve a refactor to make it clearer or a v2 API that works on a
                        #       single course and use `instructor/views/api.py:students_update_enrollment` directly.
                        # Ensuring the course is linked to an organization. It's somewhat a legacy code, keeping
                        # it just in case.
                        # _site = get_site_for_course(course_id)
                        # _org = OrganizationCourse.objects.get(course_id=str(course_id))

                        if email_learners:
                            email_params = get_email_params(course=get_course_by_id(course_key),
                                                            auto_enroll=auto_enroll,
                                                            secure=request.is_secure())
                        else:
                            email_params = {}

                        if action == 'enroll':
                            results += enroll_learners_in_course(
                                course_id=course_key,
                                identifiers=identifiers,
                                enroll_func=partial(
                                    enroll_email,
                                    auto_enroll=auto_enroll,
                                    email_students=email_learners,
                                    email_params=email_params,
                                ),
                                request_user=request.user,
                            )
                        else:
                            results += unenroll_learners_in_course(
                                course_id=course_key,
                                identifiers=identifiers,
                                unenroll_func=partial(
                                    unenroll_email,
                                    email_students=email_learners,
                                    email_params=email_params,
                                ),
                                request_user=request.user,
                            )

                    response_data = {
                        'auto_enroll': serializer.data.get('auto_enroll'),
                        'email_learners': serializer.data.get('email_learners'),
                        'action': serializer.data.get('action'),
                        'courses': serializer.data.get('courses'),
                        'results': results,
                    }
                else:
                    # Only 'enroll' and 'unenroll` are supported.
                    response_data = {
                        'error': 'action-not-supported',
                        'action_not_supported': action
                    }
                    response_code = status.HTTP_400_BAD_REQUEST
        else:
            # Don't do bulk enrollment. Return serializer error as response body
            response_data = serializer.errors
            response_code = status.HTTP_400_BAD_REQUEST

        return Response(response_data, status=response_code)


class UserIndexViewSet(TahoeAuthMixin, viewsets.ReadOnlyModelViewSet):
    """Provides course information

    To provide data for all learners on your site::

        GET /tahoe/api/v1/users/

    To provide details on a specific learner:

        GET /tahoe/api/v1/users/<user id>/

    """
    model = get_user_model()
    pagination_class = TahoeLimitOffsetPagination
    serializer_class = UserIndexSerializer
    throttle_classes = (TahoeAPIUserThrottle,)
    filter_backends = (DjangoFilterBackend, )
    filterset_class = UserIndexFilter

    @beeline.traced(name="apis.v1.views.UserIndexViewSet.get_queryset")
    def get_queryset(self):
        site = django.contrib.sites.shortcuts.get_current_site(self.request)
        queryset = get_users_for_site(site)
        return queryset
