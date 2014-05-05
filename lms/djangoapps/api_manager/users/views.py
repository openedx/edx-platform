""" API implementation for user-oriented interactions. """

import logging

from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.core.validators import validate_email, validate_slug, ValidationError
from django.conf import settings
from django.utils.translation import get_language, ugettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api_manager.models import GroupProfile
from api_manager.permissions import ApiKeyHeaderPermission
from courseware import module_render
from courseware.model_data import FieldDataCache
from courseware.views import get_module_for_descriptor, save_child_position, get_current_child
from lang_pref import LANGUAGE_KEY
from student.models import CourseEnrollment, PasswordHistory, UserProfile
from openedx.core.djangoapps.user_api.models import UserPreference
from xmodule.modulestore.django import modulestore
from util.password_policy_validators import (
    validate_password_length, validate_password_complexity,
    validate_password_dictionary
)
from util.bad_request_rate_limiter import BadRequestRateLimiter

log = logging.getLogger(__name__)
AUDIT_LOG = logging.getLogger("audit")

def _generate_base_uri(request):
    """
    Constructs the protocol:host:path component of the resource uri
    """
    protocol = 'http'
    if request.is_secure():
        protocol = protocol + 's'
    resource_uri = '{}://{}{}'.format(
        protocol,
        request.get_host(),
        request.get_full_path()
    )
    return resource_uri

def _serialize_user(response_data, user):
    """
    Loads the object data into the response dict
    This should probably evolve to use DRF serializers
    """
    response_data['email'] = user.email
    response_data['username'] = user.username
    response_data['first_name'] = user.first_name
    response_data['last_name'] = user.last_name
    response_data['id'] = user.id
    response_data['is_active'] = user.is_active
    return response_data

def _save_module_position(request, user, course_id, course_descriptor, position):
    """
    Records the indicated position for the specified course
    Really no reason to generalize this out of user_courses_detail aside from pylint complaining
    """
    field_data_cache = FieldDataCache([course_descriptor], course_id, user)
    if course_id == position['parent_module_id']:
        parent_module = get_module_for_descriptor(
            user,
            request,
            course_descriptor,
            field_data_cache,
            course_id
        )
    else:
        parent_module = module_render.get_module(
            user,
            request,
            position['parent_module_id'],
            field_data_cache,
            course_id
        )
    child_module = module_render.get_module(
        user,
        request,
        position['child_module_id'],
        field_data_cache,
        course_id
    )
    save_child_position(parent_module, child_module.location.name)
    saved_module = get_current_child(parent_module)
    return saved_module.id


class UsersList(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def post(self, request, format=None):
        """
        POST creates a new user in the system
        """
        response_data = {}
        base_uri = _generate_base_uri(request)
        email = request.DATA['email']
        username = request.DATA['username']
        password = request.DATA['password']
        first_name = request.DATA.get('first_name', '')
        last_name = request.DATA.get('last_name', '')
        is_active = request.DATA.get('is_active', None)

        # enforce password complexity as an optional feature
        if settings.FEATURES.get('ENFORCE_PASSWORD_POLICY', False):
            try:
                validate_password_length(password)
                validate_password_complexity(password)
                validate_password_dictionary(password)
            except ValidationError, err:
                status_code = status.HTTP_400_BAD_REQUEST
                response_data['message'] = _('Password: ') + '; '.join(err.messages)
                return Response(response_data, status=status_code)
        try:
            validate_email(email)
        except ValidationError:
            status_code = status.HTTP_400_BAD_REQUEST
            response_data['message'] = _('Valid e-mail is required.')
            return Response(response_data, status=status_code)

        try:
            validate_slug(username)
        except ValidationError:
            status_code = status.HTTP_400_BAD_REQUEST
            response_data['message'] = _('Username should only consist of A-Z and 0-9, with no spaces.')
            return Response(response_data, status=status_code)

        # Create the User, UserProfile, and UserPreference records
        try:
            user = User.objects.create(email=email, username=username)
        except IntegrityError:
            user = None
        else:
            user.set_password(password)
            user.first_name = first_name
            user.last_name = last_name
            if is_active is not None:
                user.is_active = is_active
            user.save()

            profile = UserProfile(user=user)
            profile.name = '{} {}'.format(first_name, last_name)
            profile.save()

            UserPreference.set_preference(user, LANGUAGE_KEY, get_language())

            # add this account creation to password history
            # NOTE, this will be a NOP unless the feature has been turned on in configuration
            password_history_entry = PasswordHistory()
            password_history_entry.create(user)

            # add to audit log
            AUDIT_LOG.info(u"API::New account created with user-id - {0}".format(user.id))

            # CDODGE:  @TODO: We will have to extend this to look in the CourseEnrollmentAllowed table and
            # auto-enroll students when they create a new account. Also be sure to remove from
            # the CourseEnrollmentAllow table after the auto-registration has taken place
        if user:
            status_code = status.HTTP_201_CREATED
            response_data = _serialize_user(response_data, user)
            response_data['uri'] = '{}/{}'.format(base_uri, str(user.id))
        else:
            status_code = status.HTTP_409_CONFLICT
            response_data['message'] = "User '%s' already exists", username
            response_data['field_conflict'] = "username"

        return Response(response_data, status=status_code)


class UsersDetail(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, user_id, format=None):
        """
        GET retrieves an existing user from the system
        """
        response_data = {}
        base_uri = _generate_base_uri(request)
        try:
            existing_user = User.objects.get(id=user_id)
            _serialize_user(response_data, existing_user)
            response_data['uri'] = base_uri
            response_data['resources'] = []
            resource_uri = '{}/groups'.format(base_uri)
            response_data['resources'].append({'uri': resource_uri})
            resource_uri = '{}/courses'.format(base_uri)
            response_data['resources'].append({'uri': resource_uri})
            return Response(response_data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, user_id, format=None):
        """
        POST provides the ability to update information about an existing user
        """
        response_data = {}
        base_uri = _generate_base_uri(request)
        response_data['uri'] = _generate_base_uri(request)
        # Add some rate limiting here by re-using the RateLimitMixin as a helper class
        limiter = BadRequestRateLimiter()
        if limiter.is_rate_limit_exceeded(request):
            AUDIT_LOG.warning("API::Rate limit exceeded in password_reset")
            response_data['message'] = _('Rate limit exceeded in password_reset.')
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)
        try:
            existing_user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            limiter.tick_bad_request_counter(request)
            existing_user = None
        if existing_user:

            is_active = request.DATA.get('is_active', None)
            if is_active is not None:
                existing_user.is_active = is_active
                response_data['is_active'] = existing_user.is_active
                existing_user.save()

            password = request.DATA.get('password')
            if password:
                old_password_hash = existing_user.password
                _serialize_user(response_data, existing_user)
                password = request.DATA['password']
                if settings.FEATURES.get('ENFORCE_PASSWORD_POLICY', False):
                    try:
                        validate_password_length(password)
                        validate_password_complexity(password)
                        validate_password_dictionary(password)
                    except ValidationError, err:
                        # bad user? tick the rate limiter counter
                        AUDIT_LOG.warning("API::Bad password in password_reset.")
                        status_code = status.HTTP_400_BAD_REQUEST
                        response_data['message'] = _('Password: ') + '; '.join(err.messages)
                        return Response(response_data, status=status_code)

                # also, check the password reuse policy
                err_msg = None
                if not PasswordHistory.is_allowable_password_reuse(existing_user, password):
                    if existing_user.is_staff:
                        num_distinct = settings.ADVANCED_SECURITY_CONFIG['MIN_DIFFERENT_STAFF_PASSWORDS_BEFORE_REUSE']
                    else:
                        num_distinct = settings.ADVANCED_SECURITY_CONFIG['MIN_DIFFERENT_STUDENT_PASSWORDS_BEFORE_REUSE']
                    err_msg = _(
                        "You are re-using a password that you have used recently. You must "
                        "have {0} distinct password(s) before reusing a previous password."
                    ).format(num_distinct)

                # also, check to see if passwords are getting reset too frequent
                if PasswordHistory.is_password_reset_too_soon(existing_user):
                    num_days = settings.ADVANCED_SECURITY_CONFIG['MIN_TIME_IN_DAYS_BETWEEN_ALLOWED_RESETS']
                    err_msg = _(
                        "You are resetting passwords too frequently. Due to security policies, "
                        "{0} day(s) must elapse between password resets"
                    ).format(num_days)

                if err_msg:
                    # We have an password reset attempt which violates some security policy,
                    status_code = status.HTTP_403_FORBIDDEN
                    response_data['message'] = err_msg
                    return Response(response_data, status=status_code)

                existing_user.is_active = True
                existing_user.set_password(password)
                existing_user.save()
                update_user_password_hash = existing_user.password

                if update_user_password_hash != old_password_hash:
                    # add this account creation to password history
                    # NOTE, this will be a NOP unless the feature has been turned on in configuration
                    password_history_entry = PasswordHistory()
                    password_history_entry.create(existing_user)

            status_code = status.HTTP_200_OK

        else:
            status_code = status.HTTP_404_NOT_FOUND
            response_data['message'] = 'User not exist'

        return Response(response_data, status=status_code)


class UsersGroupsList(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def post(self, request, user_id, format=None):
        """
        POST creates a new user-group relationship in the system
        """
        response_data = {}
        group_id = request.DATA['group_id']
        base_uri = _generate_base_uri(request)
        response_data['uri'] = '{}/{}'.format(base_uri, str(group_id))
        try:
            existing_user = User.objects.get(id=user_id)
            existing_group = Group.objects.get(id=group_id)
        except ObjectDoesNotExist:
            existing_user = None
            existing_group = None
        if existing_user and existing_group:
            try:
                existing_relationship = existing_user.groups.get(id=existing_group.id)
            except ObjectDoesNotExist:
                existing_relationship = None
            if existing_relationship is None:
                existing_user.groups.add(existing_group.id)
                response_data['uri'] = '{}/{}'.format(base_uri, existing_user.id)
                response_data['group_id'] = str(existing_group.id)
                response_data['user_id'] = str(existing_user.id)
                response_status = status.HTTP_201_CREATED
            else:
                response_data['uri'] = '{}/{}'.format(base_uri, existing_group.id)
                response_data['message'] = "Relationship already exists."
                response_status = status.HTTP_409_CONFLICT
        else:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=response_status)

    def get(self, request, user_id, format=None):
        """
        GET retrieves the list of groups related to the specified user
        """
        try:
            existing_user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return Response({}, status.HTTP_404_NOT_FOUND)
        groups = existing_user.groups.all()
        response_data = {}
        response_data['groups'] = []
        for group in groups:
            group_profile = GroupProfile.objects.get(group_id=group.id)
            group_data = {}
            group_data['id'] = group.id
            group_data['name'] = group_profile.name
            response_data['groups'].append(group_data)
        response_status = status.HTTP_200_OK
        return Response(response_data, status=response_status)


class UsersGroupsDetail(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, user_id, group_id, format=None):
        """
        GET retrieves an existing user-group relationship from the system
        """
        response_data = {}
        base_uri = _generate_base_uri(request)
        try:
            existing_user = User.objects.get(id=user_id, is_active=True)
            existing_relationship = existing_user.groups.get(id=group_id)
        except ObjectDoesNotExist:
            existing_user = None
            existing_relationship = None
        if existing_user and existing_relationship:
            response_data['user_id'] = existing_user.id
            response_data['group_id'] = existing_relationship.id
            response_data['uri'] = base_uri
            response_status = status.HTTP_200_OK
        else:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=response_status)

    def delete(self, request, user_id, group_id, format=None):
        """
        DELETE removes/inactivates/etc. an existing user-group relationship
        """
        existing_user = User.objects.get(id=user_id, is_active=True)
        existing_user.groups.remove(group_id)
        existing_user.save()
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class UsersCoursesList(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def post(self, request, user_id, format=None):
        """
        POST creates a new course enrollment for a user
        """
        store = modulestore()
        response_data = {}
        user_id = user_id
        course_id = request.DATA['course_id']
        try:
            user = User.objects.get(id=user_id)
            course_descriptor = store.get_course(course_id)
        except (ObjectDoesNotExist, ValueError):
            user = None
            course_descriptor = None
        if user and course_descriptor:
            base_uri = _generate_base_uri(request)
            course_enrollment = CourseEnrollment.enroll(user, course_id)
            response_data['uri'] = '{}/{}'.format(base_uri, course_id)
            response_data['id'] = course_id
            response_data['name'] = course_descriptor.display_name
            response_data['is_active'] = course_enrollment.is_active
            status_code = status.HTTP_201_CREATED
        else:
            status_code = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=status_code)

    def get(self, request, user_id, format=None):
        """
        GET creates the list of enrolled courses for a user
        """
        store = modulestore()
        response_data = []
        base_uri = _generate_base_uri(request)
        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            user = None
        if user:
            enrollments = CourseEnrollment.enrollments_for_user(user=user)
            for enrollment in enrollments:
                descriptor = store.get_course(enrollment.course_id)
                course_data = {
                    "id": enrollment.course_id,
                    "uri": '{}/{}'.format(base_uri, enrollment.course_id),
                    "is_active": enrollment.is_active,
                    "name": descriptor.display_name
                }
                response_data.append(course_data)
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            status_code = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=status_code)


class UsersCoursesDetail(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def post(self, request, user_id, course_id, format=None):
        """
        POST creates an ACTIVE course enrollment for the specified user
        """
        store = modulestore()
        base_uri = _generate_base_uri(request)
        response_data = {}
        response_data['uri'] = base_uri
        try:
            user = User.objects.get(id=user_id)
            course_descriptor = store.get_course(course_id)
        except (ObjectDoesNotExist, ValueError):
            user = None
            course_descriptor = None
        if user and course_descriptor:
            response_data['user_id'] = user.id
            response_data['course_id'] = course_id
            response_status = status.HTTP_201_CREATED
            if request.DATA['position']:
                response_data['position'] = _save_module_position(
                    request,
                    user,
                    course_id,
                    course_descriptor,
                    request.DATA['position']
                )
        else:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=response_status)

    def get(self, request, user_id, course_id, format=None):
        """
        GET identifies an ACTIVE course enrollment for the specified user
        """
        store = modulestore()
        response_data = {}
        base_uri = _generate_base_uri(request)
        try:
            user = User.objects.get(id=user_id, is_active=True)
            course_descriptor = store.get_course(course_id)
        except (ObjectDoesNotExist, ValueError):
            user = None
            course_descriptor = None
        if user and CourseEnrollment.is_enrolled(user, course_id):
            response_data['user_id'] = user.id
            response_data['course_id'] = course_id
            response_data['uri'] = base_uri
            field_data_cache = FieldDataCache([course_descriptor], course_id, user)
            course_module = module_render.get_module(
                user,
                request,
                course_descriptor.location,
                field_data_cache,
                course_id)
            response_data['position'] = course_module.position
            response_status = status.HTTP_200_OK
        else:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=response_status)

    def delete(self, request, user_id, course_id, format=None):
        """
        DELETE unenrolls the specified user from a course
        """
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except ObjectDoesNotExist:
            user = None
        if user:
            CourseEnrollment.unenroll(user, course_id)
        return Response({}, status=status.HTTP_204_NO_CONTENT)
